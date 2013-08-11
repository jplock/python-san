#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3
import optparse

from san.config import *
from san.parser.array import Array
from san.parser.masking import Masking
from san.parser.disk import Disk

def connect(filename):
    create = not os.path.exists(filename)
    db = sqlite3.connect(filename)
    if create:
        db.execute("CREATE TABLE array ("
            "symid TEXT PRIMARY KEY UNIQUE NOT NULL, "
            "symapi TEXT NOT NULL, "
            "model TEXT NOT NULL, "
            "microcode TEXT NOT NULL, "
            "cache_MB INTEGER NOT NULL, "
            "disks INTEGER NOT NULL)")
        db.execute("CREATE TABLE masking ("
            "symid TEXT NOT NULL, "
            "dev TEXT NOT NULL, "
            "initiator TEXT NOT NULL, "
            "PRIMARY KEY(symid, dev, initiator), "
            "FOREIGN KEY(symid) REFERENCES array(symid) "
            "ON UPDATE CASCADE ON DELETE CASCADE)")
        db.execute("CREATE TABLE disk ("
            "symid TEXT NOT NULL, "
            "bus TEXT NOT NULL, "
            "raid_group TEXT NOT NULL, "
            "model TEXT NOT NULL, "
            "total_MB INTEGER NOT NULL, "
            "free_MB INTEGER NOT NULL, "
            "PRIMARY KEY(symid, bus), "
            "FOREIGN KEY(symid) REFERENCES array(symid) "
            "ON UPDATE CASCADE ON DELETE CASCADE)")
        db.execute("CREATE TABLE dev_tier ("
            "symid TEXT NOT NULL, "
            "dev TEXT NOT NULL, "
            "end_offset_MB INTEGER NOT NULL, "
            "tier TEXT NOT NULL, "
            "PRIMARY KEY(symid, dev), "
            "FOREIGN KEY(symid) REFERENCES array(symid) "
            "ON UPDATE CASCADE ON DELETE CASCADE)")
        db.commit()
    return db

def main():
    db = connect(DB_FILE)

    parser = Array(db)
    all_symids = {}

    for symapi in SYMAPI_SERVERS:
        parser.clear(symapi)
        filename = ".".join(["symcfg-list", symapi, "xml"])
        file_path = os.path.join(TMP_DIR, filename)
        print(file_path)
        all_symids[symapi] = parser.parse(symapi, file_path)

    #parser = Masking(db)
    #for symapi, symids in all_symids.items():
    #    for symid in symids:
    #        parser.clear(symid)
    #        filename = ".".join(["symmaskdb", symid, symapi, "xml"])
    #        file_path = os.path.join(TMP_DIR, filename)
    #        print(file_path)
    #        parser.parse(file_path)

    parser = Disk(db)
    for symapi, symids in all_symids.items():
        filename = ".".join(["symdisk", symapi, "xml"])
        file_path = os.path.join(TMP_DIR, filename)
        print(file_path)
        for symid in symids:
            parser.clear(symid)
            parser.parse(file_path)

    db.close()

if __name__ == "__main__":
    main()