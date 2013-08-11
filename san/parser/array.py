# -*- coding: utf-8 -*-

import os
import sqlite3
import xml.sax
import xml.sax.handler

class ArraySaxHandler(xml.sax.handler.ContentHandler):

    def __init__(self, db, symapi):
        super(ArraySaxHandler, self).__init__()
        self._data = {}
        self._text = []
        self._db = db
        self._symapi = symapi
        self._in_code = False
        self.symids = []

    def startElement(self, name, attributes):
        if name == "Symmetrix":
            self._data = {}
        elif name == "Microcode":
            self._in_code = True
        self._text = []

    def endElement(self, name):
        fields = ("symid", "product_model", "version",
                  "disks", "megabytes", "patch_level")
        if name in fields:
            content = "".join(self._text)
            if name == "version" and not self._in_code:
                return
            elif name == "product_model":
                name = "model"
            elif name == "symid":
                self.symids.append(content)
            self._data[name] = content
        elif name == "Microcode":
            self._data["microcode"] = self._data["version"] + "." + self._data["patch_level"]
            del self._data["version"], self._data["patch_level"]
            self._in_code = False
        elif name == "Symmetrix":
            self._data["symapi"] = self._symapi
            self._db.execute("INSERT INTO array "
                "(symid, symapi, model, microcode, cache_MB, disks) VALUES "
                "(:symid, :symapi, :model, :microcode, :megabytes, :disks)",
                self._data)
            self._db.commit()
            self._data = {}
        self._text = []

    def characters(self, text):
        self._text.append(text)

class Array():

    def __init__(self, db):
        self._db = db

    def clear(self, symapi):
        try:
            self._db.execute("DELETE FROM array WHERE symapi=?", (symapi,))
            self._db.commit()
        except ValueError as err:
            pass

    def parse(self, symapi, filename):
        try:
            handler = ArraySaxHandler(self._db, symapi)
            parser = xml.sax.make_parser()
            parser.setContentHandler(handler)
            parser.parse(filename)
            return handler.symids
        except (EnvironmentError, ValueError, xml.sax.SAXParseException) as err:
            print("{0}: import error: {1}".format(
                os.path.basename(filename), err))
            return False