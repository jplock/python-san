# -*- coding: utf-8 -*-

import os
import subprocess

def get_process_output(output_file, cmd):
    with open(output_file, "w") as fp:
        pipe = subprocess.Popen(
            cmd.split(" "),
            stdout=fp,
            env=os.environ
        )
        pipe.wait()