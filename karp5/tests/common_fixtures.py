from distutils.util import strtobool
import os

import pytest

from click.testing import CliRunner

import elasticsearch_test

from karp5.config import conf_mgr
from karp5.cli import cli as karp5_cli
from karp5.cli import setup_cli
from karp5.tests import auth_server
from karp5.tests._test_config import TestConfig


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(name="es", scope="session")
def fixture_es():
    if not strtobool(os.environ.get("ELASTICSEARCH_ENABLED", "false")):
        yield False
    elif os.environ.get("KARP5_ELASTICSEARCH_TEST_URL"):
        yield True
    else:
        if not os.environ.get("ES_HOME"):
            raise RuntimeError("must set $ES_HOME to run tests that use elasticsearch")
        with elasticsearch_test.ElasticsearchTest(port=9201):
            yield True


class CliTestRunner(object):
    def __init__(self, _cli):
        self.runner = CliRunner()
        self.cli = _cli

    def create_empty_index(self, mode, suffix):
        return self.runner.invoke(self.cli, ["create_empty_index", mode, suffix])

    def create_mode(self, mode, suffix):
        return self.runner.invoke(self.cli, ["create_mode", mode, suffix])

    def publish_mode(self, mode, suffix):
        return self.runner.invoke(self.cli, ["publish_mode", mode, suffix])

    def reindex_alias(self, mode, suffix):
        return self.runner.invoke(self.cli, ["reindex_alias", mode, suffix])

    def lexicon_init(self, lexicon: str, suffix: str, data=None):
        """[summary]

        Arguments:
            lexicon {str} -- [description]
            suffix {str} -- [description]

        Keyword Arguments:
            data {[type]} -- [description] (default: {None})
        """
        cmd = ["lexicon", "init", lexicon, suffix]
        if data is not None:
            cmd.append("--data")
            cmd.append(data)
        return self.runner.invoke(self.cli, cmd)


@pytest.fixture(name="cli", scope="session")
def fixture_cli():
    setup_cli(TestConfig)
    cli = CliTestRunner(karp5_cli)
    return cli


@pytest.fixture(name="cli_w_es", scope="session")
def fixture_cli_w_es(cli, es):
    if not es:
        pytest.skip("elasticsearch disabled")
    yield cli


@pytest.fixture(name="app_w_auth", scope="session")
def fixture_app_w_auth(app):

    with auth_server.DummyAuthServer(conf_mgr, port=5001):
        yield app
