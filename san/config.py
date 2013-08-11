# -*- coding: utf-8 -*-

import os

SAN_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SAN_DIR, "data")
TMP_DIR = os.path.join(SAN_DIR, "tmp")
DB_FILE = os.path.join(DATA_DIR, "san.db3")
LOG_FILE = os.path.join(DATA_DIR, "san.log")

NUM_COLLECTORS = 8
SYMAPI_SERVERS = (
    "SYMAPI_SERVER"
)
CLARIION_DOMAINS = (
    {"ip": "127.0.0.1", "username": "Admin", "password": "Test", "domain": True}
)
INVISTA_CLUSTERS = (
    {"ip": "127.0.0.1", "username": "storageadmin", "password": "Test"},
)
CISCO_SWITCHES = (
    {"ip": "127.0.0.1", "username": "admin", "password": "Test"}
)