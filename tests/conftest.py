from __future__ import unicode_literals
import logging
import os
import tempfile

import pytest

# import dotenv
# dotenv.load_dotenv(dotenv_path='.env', verbose=True)
os.environ['KARP_INSTANCE_PATH'] = os.path.join(
    os.path.dirname(__file__),
    'data/'
)
from karp5 import create_app, Config


_tempfile = tempfile.NamedTemporaryFile(suffix='.db')

class TestConfig(Config):
    TESTING = True
    LOG_LEVEL = logging.WARNING
    DATABASE_BASEURL = 'sqlite://' + _tempfile.name + '/{}'


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)

    return app


@pytest.fixture(scope="session")
def real_app():
    app = create_app()

    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
