import logging
import os
import tempfile
import time
from distutils.util import strtobool

import pytest

from click.testing import CliRunner

import elasticsearch_test

import dotenv
dotenv.load_dotenv(dotenv_path='.env', verbose=True)
os.environ['KARP_INSTANCE_PATH'] = os.path.join(
    os.path.dirname(__file__),
    'data/'
)
from karp5 import create_app, Config
from karp5.cli import upload_offline as upload, cli as karp5_cli, setup_cli
from karp5.config import mgr as conf_mgr


_tempfile = tempfile.NamedTemporaryFile(suffix='.db')

class TestConfig(Config):
    TESTING = True
    LOG_LEVEL = logging.DEBUG
    DATABASE_BASEURL = 'sqlite://'
    ELASTICSEARCH_URL='localhost:9201'


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)

    return app


# @pytest.fixture(scope="session")
# def real_app():
#     app = create_app()
#
#     return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def es():
    if not strtobool(os.environ.get('ELASTICSEARCH_ENABLED', 'false')):
        yield False
    else:
        if not os.environ.get('ES_HOME'):
            raise RuntimeError('must set $ES_HOME to run tests that use elasticsearch')
        with elasticsearch_test.ElasticsearchTest(port=9201):
            yield True


class CliTestRunner(object):
    def __init__(self, cli):
        self.runner = CliRunner()
        self.cli = cli

    def create_empty_index(self, mode, suffix):
        return self.runner.invoke(self.cli, ['create_empty_index', mode, suffix])

    def create_mode(self, mode, suffix):
        return self.runner.invoke(self.cli, ['create_mode', mode, suffix])

    def publish_mode(self, mode, suffix):
        return self.runner.invoke(self.cli, ['publish_mode', mode, suffix])

    def reindex_alias(self, mode, suffix):
        return self.runner.invoke(self.cli, ['reindex_alias', mode, suffix])


@pytest.fixture(scope='session')
def cli():
    setup_cli(TestConfig)
    cli = CliTestRunner(karp5_cli)
    return cli


@pytest.fixture(scope='session')
def cli_w_es(cli, es):
    if not es:
        pytest.skip('elasticsearch disabled')
    return cli


@pytest.fixture(scope='session')
def cli_w_panacea(cli_w_es):
    r_create = cli_w_es.create_mode('panacea', 'test')
    assert r_create.exit_code == 0

    r_publish = cli_w_es.publish_mode('panacea', 'test')
    assert r_publish.exit_code == 0

    time.sleep(1)
    return cli_w_es

@pytest.fixture(scope='session')
def app_w_auth(app):
    import auth_server
    with auth_server.DummyAuthServer(conf_mgr, port=5001):
        yield app

@pytest.fixture(scope='session')
def app_w_panacea(app_w_auth, cli_w_panacea):

    return app_w_auth


@pytest.fixture(scope='session')
def client_w_panacea(app_w_panacea):
    return app_w_panacea.test_client()
