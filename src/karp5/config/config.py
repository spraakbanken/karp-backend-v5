from __future__ import unicode_literals
from builtins import object

from distutils.util import strtobool

import json
import logging
import os

from karp5.instance_info import get_instance_path


with open(os.path.join(get_instance_path(), 'config/config.json')) as fp:
    _config = json.load(fp)


class Config(object):
    DEBUG = False
    TESTING = False
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
    ELASTICSEARCH_URL = os.environ.get('KARP5_ELASTICSEARCH_URL', 'http://localhost:9200').split(',')
    OVERRIDE_ELASTICSEARCH_URL = strtobool(os.environ.get('KARP5_ELASTICSEARCH_URL_OVERRIDE', 'false'))
    TESTING = False
    DEBUG = False
    DATABASE_BASEURL = (
        'mysql+pymysql://{}/'.format(
            _config['DB']['DBPASS']
        ) + '{}?charset=utf8'
    )
    STANDARDMODE = _config['SETUP']['STANDARDMODE']
