# -*- coding: utf-8 -*-

import os
import subprocess
import multiprocessing

import paramiko

from san.config import *

COMMANDS = (
    "show zoneset active"
)

class CiscoWorker(multiprocessing.Process):
    def __init__(self, work_queue, number):
        super(CiscoWorker, self).__init__()
        self._queue = work_queue
        self._number = number

    def run(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            for switch, cmd in iter(self._queue.get, "STOP"):
                output_filename = "_".join(["cisco", switch["ip"], "zoneset"]) + ".txt"
                output_file = os.path.join(TMP_DIR, output_filename)

                ssh.connect(
                    switch["ip"],
                    username=switch["username"],
                    password=switch["password"]
                )
                stdin, stdout, stderr = ssh.exec_command(cmd)

                with open(output_file, "w") as fp:
                    fp.write(stdout)
                ssh.close()
        finally:
            self.__queue.task_done()

class Cisco():
    def __init__(self, switches):
        self._switches = switches
        self._arrays = []

    def collect(self):
        if not HAS_SSH:
            return False
        if not self._switches:
            return False

        work_queue = multiprocessing.JoinableQueue()
        workers = []

        for switch in self._switches:
            for cmd in COMMANDS:
                work_queue.put([switch, cmd.format(**switch)])

        for i in range(NUM_COLLECTORS):
            worker = CiscoWorker(work_queue, i)
            worker.daemon = True
            worker.start()
            workers.append(worker)
            work_queue.put("STOP")

        for worker in workers:
            worker.join()

        return True