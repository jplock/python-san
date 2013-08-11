# -*- coding: utf-8 -*-

import os
import subprocess
import multiprocessing

from san.config import *
from san.collector.common import get_process_output

COMMANDS = {
    "getagent": "invseccli -User {username} -h {ip} getagent -serial",
    "seinfo": "invseccli -User {username} -h {ip} seinfo -getallSEsinfo -pathatt",
    "volume": "invseccli -User {username} -h {ip} volume -list",
    "virtframe": "invseccli -User {username} -h {ip} virtframe -list"
}

class InvistaWorker(multiprocessing.Process):
    def __init__(self, work_queue, number):
        super(InvistaWorker, self).__init__()
        self._queue = work_queue
        self._number = number

    def run(self):
        try:
            for node, brief_cmd, full_cmd in iter(self._queue.get, "STOP"):
                output_filename = "_".join([brief_cmd, node]) + ".txt"
                output_file = os.path.join(TMP_DIR, output_filename)
                get_process_output(output_file, full_cmd)
        finally:
            self._queue.task_done()

class Invista():
    def __init__(self, clusters):
        self._clusters = clusters
        self._arrays = {}

    def get_arrays(self):
        if self._arrays:
            return self._arrays

        cmd = "invseccli -User {username} -h {ip} getagent -serial"

        for cluster in self._clusters:
            node_cmd = cmd.format(**cluster)

            pipe = subprocess.Popen(
                node_cmd.split(" "),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            print("CMD:", node_cmd)
            #pipe.wait()
            print("IN:", cluster["password"].encode("utf8") + b"\r\n")
            pipe.stdin.write(cluster["password"].encode("utf8") + b"\r\n")
            result = pipe.stdout.readline()
            print("OUT:", result)
            #pipe.wait()

            #(stdoutdata, stderrdata) = pipe.communicate(input=cluster["password"].encode("utf8"))

            #for data in pipe.stdout:
            #    print("OUT:", data)
            #print("OUT:", stdoutdata)
            #print("ERR:", stderrdata)
            #lines = stdoutdata.decode("utf8")
            #print(lines)



            #for data in pipe.stdout:
            #    line = data.decode("utf8").strip()
            #    pair = line.split(":", 2)
            #    if pair[0] == "Node":
            #        node_name = pair[1].lstrip()
            #    elif pair[0] == "IP Address":
            #        ip = pair[1].lstrip()

            #        node = {
            #            "ip": ip,
            #            "node": node_name,
            #            "username": cluster["username"],
            #            "password": cluster["password"]
            #        }
            #        self.__arrays.append(sp)

        return self.__arrays

    def collect(self):
        found_arrays = self.get_arrays()
        if not found_arrays:
            return False

        work_queue = multiprocessing.JoinableQueue()
        workers = []

        for node in found_arrays:
            for brief_cmd, full_cmd in COMMANDS.items():
                work_queue.put([node, brief_cmd, full_cmd.format(**node)])

        for i in range(NUM_COLLECTORS):
            worker = InvistaWorker(work_queue, i)
            worker.daemon = True
            worker.start()
            workers.append(worker)
            work_queue.put("STOP")

        for worker in workers:
            worker.join()

        return True