import logging
import os
import tempfile

from karp5 import Config


KARP5_DBPASS = os.environ.get("KARP5_DBPASS")

_tempfile = tempfile.NamedTemporaryFile(suffix=".db")


class TestConfig(Config):
    TESTING = True
    LOG_LEVEL = logging.INFO
    if KARP5_DBPASS is None:
        # Use sqlite if KARP5_DBPASS is not set
        # DATABASE_BASEURL = "sqlite://"
        DATABASE_BASEURL = f"sqlite:///{_tempfile.name}"
    ELASTICSEARCH_URL = os.environ.get("KARP5_ELASTICSEARCH_TEST_URL") or "localhost:9201"
    OVERRIDE_ELASTICSEARCH_URL = True
