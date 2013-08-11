# -*- coding: utf-8 -*-

import os
import subprocess
import multiprocessing

from lxml import etree

from san.config import *
from san.collector.common import get_process_output

COMMANDS = {
    #"symcfg": "symcfg list -output xml",
    "symcfg-list": "symcfg -v list -output xml",
    #"symdev": "symdev -v list -output xml",
    "symdisk": "symdisk -v -hypers list -output xml",
    #"symcfg-FA": "symcfg -FA ALL list -output xml",
    #"symcfg-FA-ALL": "symcfg -FA ALL -address list -output xml"
}
SYM_COMMANDS = {
    "symmaskdb": "symmaskdb -sid {0} list database -output xml",
}

def init_environment(symapi):
    if not symapi:
        return None
    os.environ["SYMCLI_CONNECT"] = symapi
    os.environ["SYMCLI_CTL_ACCESS"] = "PARALLEL"
    os.environ["SYMCLI_CONNECT_TYPE"] = "REMOTE_CACHED"
    os.environ["SYMCLI_OFFLINE"] = "1"

class SymmetrixWorker(multiprocessing.Process):
    def __init__(self, work_queue, number):
        super(SymmetrixWorker, self).__init__()
        self._queue = work_queue
        self._number = number

    def run(self):
        try:
            for symapi, brief_cmd, full_cmd in iter(self._queue.get, "STOP"):
                init_environment(symapi)

                output_filename = ".".join([brief_cmd, symapi]) + ".xml"
                output_file = os.path.join(TMP_DIR, output_filename)
                get_process_output(output_file, full_cmd)
        finally:
            self._queue.task_done()

class Symmetrix():
    def __init__(self, symapis):
        self._symapis = symapis
        self._arrays = {}

    def get_arrays(self, symapi=None, rediscover=False):
        if self.__arrays:
            if symapi and self._arrays[symapi]:
                return self._arrays[symapi]
            else:
                return self._arrays

        parser = etree.XMLParser(remove_blank_text=True)
        find = etree.XPath("//symid/text()")

        for symapi in self._symapis:
            init_environment(symapi)

            if rediscover:
                os.environ["SYMCLI_OFFLINE"] = "0"
                retcode = subprocess.call(
                    ["symcfg", "discover"],
                    env=os.environ
                )
                os.environ["SYMCLI_OFFLINE"] = "1"

            cmd = "symcfg list -output xml"
            pipe = subprocess.Popen(
                cmd.split(" "),
                stdout=subprocess.PIPE,
                env=os.environ
            )
            (stdoutdata, stderrdata) = pipe.communicate()

            root = etree.fromstring(stdoutdata, parser)
            self._arrays[symapi] = find(root)
        return self._arrays

    def collect(self, rediscover=False):
        found_arrays = self.get_arrays(rediscover=rediscover)
        if not found_arrays:
            return False

        work_queue = multiprocessing.JoinableQueue()
        workers = []

        for symapi, arrays in found_arrays.items():
            for brief_cmd, full_cmd in COMMANDS.items():
                work_queue.put([symapi, brief_cmd, full_cmd])
            for array in arrays:
                for brief_cmd, full_cmd in SYM_COMMANDS.items():
                    brief_cmd = brief_cmd + "." + array
                    work_queue.put([symapi, brief_cmd, full_cmd.format(array)])

        for i in range(NUM_COLLECTORS):
            worker = SymmetrixWorker(work_queue, i)
            worker.daemon = True
            worker.start()
            workers.append(worker)
            work_queue.put("STOP")

        for worker in workers:
            worker.join()

        return True