# -*- coding: utf-8 -*-

import os
import subprocess
import multiprocessing

from san.config import *
from san.collector.common import get_process_output

COMMANDS = {
    "storagegroup": "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} storagegroup -list -host",
    "getlun": "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} getlun -capacity -rg -type",
    "getdisk": "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} getdisk -capacity -product -usercapacity -rg",
    "metalun": "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} metalun -list -name -components",
    "port": "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} port -list -sp",
    "getagent": "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} getagent -rev -mem -model"
}

class ClariionWorker(multiprocessing.Process):
    def __init__(self, work_queue, number):
        super(ClariionWorker, self).__init__()
        self._queue = work_queue
        self._number = number

    def run(self):
        try:
            for sp, brief_cmd, full_cmd in iter(self._queue.get, "STOP"):
                output_filename = ".".join([brief_cmd, sp["node"], sp["ip"]]) + ".txt"
                output_file = os.path.join(TMP_DIR, output_filename)
                get_process_output(output_file, full_cmd)
        finally:
            self._queue.task_done()

class Clariion():
    def __init__(self, domains):
        self._domains = domains
        self._arrays = []

    def get_arrays(self):
        if self._arrays:
            return self._arrays

        for domain in self.__domains:
            if not domain["domain"]:
                cmd = "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} getagent -serial"
            else:
                cmd = "naviseccli -Scope 0 -User {username} -Password {password} -h {ip} domain -list"

            cmd = cmd.format(**domain)

            pipe = subprocess.Popen(
                cmd.split(" "),
                stdout=subprocess.PIPE
            )
            pipe.wait()

            for data in pipe.stdout:
                line = data.decode("utf8").strip()
                pair = line.split(":", 2)
                if pair[0] == "Node":
                    node_name = pair[1].lstrip()
                elif pair[0] == "IP Address":
                    ip = pair[1].lstrip()
                    if ip.endswith(" (Master)"):
                        ip = ip[0:-9]

                    sp = {
                        "ip": ip,
                        "node": node_name,
                        "username": domain["username"],
                        "password": domain["password"]
                    }
                    self._arrays.append(sp)

        return self._arrays

    def collect(self):
        found_arrays = self.get_arrays()
        if not found_arrays:
            return False

        work_queue = multiprocessing.JoinableQueue()
        workers = []

        for sp in found_arrays:
            for brief_cmd, full_cmd in COMMANDS.items():
                work_queue.put([sp, brief_cmd, full_cmd.format(**sp)])

        for i in range(NUM_COLLECTORS):
            worker = ClariionWorker(work_queue, i)
            worker.daemon = True
            worker.start()
            workers.append(worker)
            work_queue.put("STOP")

        for worker in workers:
            worker.join()

        return True