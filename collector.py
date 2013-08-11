#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse

from san.config import *
HAS_SSH = True
try:
    from san.collector.cisco import Cisco
except ImportError as e:
    HAS_SSH = False
from san.collector.symmetrix import Symmetrix
from san.collector.clariion import Clariion
from san.collector.invista import Invista

def main():
    parser = optparse.OptionParser()
    parser.add_option("-s", "--symmetrix", action="store_true", dest="symmetrix",
                      default=False, help="include SYMMETRIX arrays")
    parser.add_option("-c", "--clariion", action="store_true", dest="clariion",
                      default=False, help="include CLARiiON arrays")
    parser.add_option("-i", "--invista", action="store_true", dest="invista",
                      default=False, help="include Invista nodes")
    if HAS_SSH:
        parser.add_option("-o", "--cisco", action="store_true", dest="cisco",
                          default=False, help="include Cisco switches")
    parser.add_option("-a", "--all", action="store_true", dest="all",
                      default=False, help="include ALL collectors")

    (opts, args) = parser.parse_args()

    if opts.symmetrix or opts.all:
        symm = Symmetrix(SYMAPI_SERVERS)
        symm.collect()
    if opts.clariion or opts.all:
        cx = Clariion(CLARIION_DOMAINS)
        cx.collect()
    if HAS_SSH and (opts.cisco or opts.all):
        cisco = Cisco(CISCO_SWITCHES)
        cisco.collect()
    if opts.invista or opts.all:
        invista = Invista(INVISTA_CLUSTERS)
        invista.collect()

if __name__ == "__main__":
    main()