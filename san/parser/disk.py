# -*- coding: utf-8 -*-

import os
import sqlite3
import xml.sax
import xml.sax.handler

TIER_MINLOOKUP = {
    "1 Database Logs": 0,
    "2 Rollback and Temp": 5,
    "3 Primary Data": 12,
    "4 Indices and Data": 41,
    "5 Log Backup Archive": 71,
    "6 Application Binaries": 91
}

TIER_MAXLOOKUP = {
    "1 Database Logs": 5,
    "2 Rollback and Temp": 11,
    "3 Primary Data": 40,
    "4 Indices and Data": 70,
    "5 Log Backup Archive": 90,
    "6 Application Binaries": 100
}

class DiskSaxHandler(xml.sax.handler.ContentHandler):

    def __init__(self, db):
        super(DiskSaxHandler, self).__init__()
        self._disk = {}
        self._hyper = {}
        self._hyper_sizes = {}
        self._bus = {}
        self._text = []
        self._db = db

    def startElement(self, name, attributes):
        if name == "Disk":
            self._disk = {}
            self._bus = {}
            self._hyper_sizes = {}
        elif name == "Hyper":
            self._hyper = {}
        self._text = []

    def endElement(self, name):
        disk_fields = ("symid", "revision", "model",
                       "avail_megabytes", "actual_megabytes")
        bus_fields = ("da_number", "interface", "tid")
        hyper_fields = ("symid", "dev_name", "megabytes", "type")
        if name in bus_fields:
            self._bus[name] = "".join(self._text)
        elif name in hyper_fields:
            self._hyper[name] = "".join(self._text)
        elif name in disk_fields:
            self._disk[name] = "".join(self._text)
        elif name == "Hyper":
            dev = self._hyper["dev_name"]
            if self._hyper_sizes[dev]:
                self._hyper_sizes[dev] += self._hyper["megabytes"]
            else:
                self._hyper_sizes[dev] = self._hyper["megabytes"]
        elif name == "Disk":
            self._disk["bus"] = self._bus["da_number"] + self._bus["interface"] \
                + format(self._bus["tid"], ">02")
            if self._hyper["type"].startswith("RAID-"):
                self._disk["raid_group"] = self._hyper["type"][4:]
            else:
                self._disk["raid_group"] = "None"
            self._db.execute("INSERT OR IGNORE INTO disk "
                "(symid, bus, raid_group, model, total_MB, free_MB) "
                "VALUES (:symid, :bus, :raid_group, :revision, "
                ":actual_megabytes, :avail_megabytes)", self._disk)
            self._db.commit()

            for hyper in sorted(self._hyper_sizes):
                self._db.execute("INSERT OR IGNORE INTO dev_tier "
                    "(symid, dev, end_offset_MB, tier) VALUES "
                    "(:symid, :dev_name, :megabytes, :tier)", hyper)
                self._db.commit()
        self._text = []

    def characters(self, text):
        self._text.append(text)

class Disk():

    def __init__(self, db):
        self._db = db

    def clear(self, symid):
        try:
            self._db.execute("DELETE FROM disk WHERE symid=?", (symid,))
            self._db.commit()
        except ValueError as err:
            pass

    def parse(self, filename):
        try:
            handler = DiskSaxHandler(self._db)
            parser = xml.sax.make_parser()
            parser.setContentHandler(handler)
            parser.parse(filename)
            return True
        except (EnvironmentError, ValueError, xml.sax.SAXParseException) as err:
            print("{0}: import error: {1}".format(
                os.path.basename(filename), err))
            return False