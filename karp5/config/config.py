"""[summary]
"""

from builtins import object

from distutils.util import strtobool

import json
import logging
import os

from karp5 import instance_info


with open(os.path.join(instance_info.get_instance_path(), "config/config.json")) as fp:
    _CONFIG = json.load(fp)

KARP5_DBPASS = os.environ.get("KARP5_DBPASS")


class Config(object):
    """[summary]"""

    DEBUG = False
    TESTING = False
    LOG_LEVEL = getattr(logging, _CONFIG["DEBUG"]["DEBUGLEVEL"].upper(), logging.WARNING)
    # LOG_LEVEL = debug_str_to_int(_CONFIG['DEBUG']['DEBUGLEVEL'])
    LOG_FMT = _CONFIG["DEBUG"].get("LOGFMT")
    LOG_DIR = _CONFIG["DEBUG"].get("LOGDIR")
    LOG_DATEFMT = _CONFIG["DEBUG"].get("DATEFMT")
    LOG_TO_STDERR = _CONFIG["DEBUG"].get("DEBUG_TO_STDERR")
    SECRET_KEY = _CONFIG["SETUP"]["SECRET_KEY"]
    ABSOLUTE_PATH = _CONFIG["SETUP"]["ABSOLUTE_PATH"]
    BACKEND_URL = _CONFIG["SETUP"].get("BACKEND_URL") or "https://ws.spraakbanken.gu.se/ws/karp/v5"
    SCRIPT_PATH = _CONFIG["SETUP"]["SCRIPT_PATH"]
    SENDER_EMAIL = _CONFIG["DB"]["SENDER_EMAIL"]
    SMTP_SERVER = _CONFIG["DB"].get("SMTP_SERVER")
    AUTH_RESOURCES = _CONFIG["AUTH"]["AUTH_RESOURCES"]
    AUTH_SECRET = _CONFIG["AUTH"]["AUTH_SECRET"]
    AUTH_SERVER = _CONFIG["AUTH"]["AUTH_SERVER"]
    ADMIN_EMAILS = _CONFIG["DB"].get("ADMIN_EMAILS")
    MAX_PAGE = _CONFIG["SETUP"]["MAX_PAGE"]
    MINIENTRY_PAGE = _CONFIG["SETUP"]["MINIENTRY_PAGE"]
    SCAN_LIMIT = _CONFIG["SETUP"]["SCAN_LIMIT"]
    ELASTICSEARCH_URL = os.environ.get("KARP5_ELASTICSEARCH_URL", "http://localhost:9200").split(
        ","
    )
    OVERRIDE_ELASTICSEARCH_URL = strtobool(
        os.environ.get("KARP5_ELASTICSEARCH_URL_OVERRIDE", "false")
    )
    TESTING = False
    DEBUG = False
    DATABASE_BASEURL = (
        f"mysql+pymysql://{KARP5_DBPASS}/" + "{}?charset=utf8"
        if KARP5_DBPASS
        else f"mysql+pymysql://{_CONFIG['DB']['DBPASS']}/" + "{}?charset=utf8"
    )
    STANDARDMODE = _CONFIG["SETUP"]["STANDARDMODE"]
