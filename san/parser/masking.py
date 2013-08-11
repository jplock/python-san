# -*- coding: utf-8 -*-

import os
import sqlite3
import xml.sax
import xml.sax.handler

class MaskingSaxHandler(xml.sax.handler.ContentHandler):

    def __init__(self, db):
        super(MaskingSaxHandler, self).__init__()
        self._data = {}
        self._text = []
        self._db = db
        self._start_dev = None
        self._end_dev = None

    def startElement(self, name, attributes):
        if name == "Db_Record":
            self._data = {}
            self._start_dev = None
            self._end_dev = None
        elif name == "Device":
            self._start_dev = None
            self._end_dev = None
        self._text = []

    def endElement(self, name):
        masking_fields = ("symid", "originator_port_wwn", "start_dev", "end_dev")
        if name in masking_fields:
            self._data[name] = "".join(self._text)
        elif name == "Device":
            if self._start_dev and self._end_dev:
                if self._start_dev == self._end_dev:
                    self._data["dev"] = self._start_dev
                    self._db.execute("INSERT OR IGNORE INTO masking "
                        "(symid, dev, initiator) VALUES "
                        "(:symid, :dev, :originator_port_wwn)", self._data)
                else:
                    start_dec = int(self._start_dev, 16)
                    end_dec = int(self._end_dev, 16) + 1
                    for num in range(start_dec, end_dec):
                        dev = format(hex(num)[2:], ">04").upper()
                        self._data["dev"] = dev
                        self._db.execute("INSERT OR IGNORE INTO masking "
                            "(symid, dev, initiator) VALUES "
                            "(:symid, :dev, :originator_port_wwn)", self._data)
                self._db.commit()
            self._start_dev = None
            self._end_dev = None
        elif name == "Db_Record":
            self._data = {}
        self._text = []

    def characters(self, text):
        self._text.append(text)

class Masking():

    def __init__(self, db):
        self._db = db

    def clear(self, symid):
        try:
            self._db.execute("DELETE FROM masking WHERE symid=?", (symid,))
            self._db.commit()
        except ValueError as err:
            pass

    def parse(self, filename):
        try:
            handler = MaskingSaxHandler(self._db)
            parser = xml.sax.make_parser()
            parser.setContentHandler(handler)
            parser.parse(filename)
            return True
        except (EnvironmentError, ValueError, xml.sax.SAXParseException) as err:
            print("{0}: import error: {1}".format(
                os.path.basename(filename), err))
            return False