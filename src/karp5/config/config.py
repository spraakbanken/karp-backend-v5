import json
import logging
import os

import six

from karp5.instance_info import get_instance_path


def debug_str_to_int(s):
    """
    Converting string to logging level. Case-insensitive.
    Defaults to logging level WARNING.

    :param s: the string to convert
    :returns: the corresponding logging.LEVEL if matching otherwise logging.WARNING
    """
    # Setting logging.WARNING as default logging level
    debuglevel = logging.WARNING
    if isinstance(s, six.text_type):
        s_lower = s.lower() # s.casefold() would be correct, but lower is sufficient


        if s_lower == "debug":
            debuglevel = logging.DEBUG
        elif s_lower == "info":
            debuglevel = logging.INFO
        elif s_lower == "warning":
            debuglevel = logging.WARNING
        elif s_lower == "error":
            debuglevel = logging.ERROR
        elif s_lower == "critical":
            debuglevel = logging.CRITICAL
        else:
            print("NOTE: Can't match debuglevel in the config file.")
            print("NOTE: Using default level: WARNING.")
    else:
        print("NOTE: Can't parse debuglevel in the config file.")
        print("NOTE: Using default level: WARNING.")
    return debuglevel


with open(os.path.join(get_instance_path(), 'config/config.json')) as fp:
    _config = json.load(fp)


class Config(object):
    LOG_LEVEL = getattr(logging, _config['DEBUG']['DEBUGLEVEL'].upper(), logging.WARNING)
    # LOG_LEVEL = debug_str_to_int(_config['DEBUG']['DEBUGLEVEL'])
    LOG_FMT = _config['DEBUG'].get('LOGFMT')
    LOG_DIR = _config['DEBUG'].get('LOGDIR')
    LOG_DATEFMT = _config['DEBUG'].get('DATEFMT')
    LOG_TO_STDERR = _config['DEBUG'].get('DEBUG_TO_STDERR')
    SECRET_KEY = _config['SETUP']['SECRET_KEY']
    ABSOLUTE_PATH = _config['SETUP']['ABSOLUTE_PATH']
    BACKEND_URL = _config['SETUP'].get('BACKEND_URL') or 'https://ws.spraakbanken.gu.se/ws/karp/v5'
    SCRIPT_PATH = _config['SETUP']['SCRIPT_PATH']
    SENDER_EMAIL = _config['DB']['SENDER_EMAIL']
    SMTP_SERVER = _config['DB'].get('SMTP_SERVER')
    AUTH_RESOURCES = _config['AUTH']['AUTH_RESOURCES']
    AUTH_SECRET = _config['AUTH']['AUTH_SECRET']
    AUTH_SERVER = _config['AUTH']['AUTH_SERVER']
    ADMIN_EMAILS = _config['DB'].get('ADMIN_EMAILS')
    MAX_PAGE = _config['SETUP']['MAX_PAGE']
    MINIENTRY_PAGE = _config['SETUP']['MINIENTRY_PAGE']
    SCAN_LIMIT = _config['SETUP']['SCAN_LIMIT']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    TESTING = False
    DEBUG = False
    DATABASE_BASEURL = (
        'mysql+pymysql://{}/'.format(
            _config['DB']['DBPASS']
        ) + '{}?charset=utf8'
    )
