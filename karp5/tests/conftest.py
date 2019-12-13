import logging
import os
import tempfile
import time
from distutils.util import strtobool

import pytest

from click.testing import CliRunner

import elasticsearch_test

import dotenv

dotenv.load_dotenv(dotenv_path=".env", verbose=True)
# os.environ["KARP5_INSTANCE_PATH"] = os.path.join(os.path.dirname(__file__), "data/")
assert os.environ["KARP5_INSTANCE_PATH"] == os.path.join(os.path.dirname(__file__), "data/")
print(os.environ["KARP5_INSTANCE_PATH"])

from karp5 import create_app, Config  # noqa: E402
from karp5.cli import cli as karp5_cli, setup_cli  # noqa: E402
from karp5.config import conf_mgr  # noqa: E402

from karp5.tests import auth_server


_tempfile = tempfile.NamedTemporaryFile(suffix=".db")

KARP5_DBPASS = os.environ.get("KARP5_DBPASS")


class TestConfig(Config):
    TESTING = True
    LOG_LEVEL = logging.DEBUG
    if KARP5_DBPASS is None:
        # Use sqlite if KARP5_DBPASS is not set
        # DATABASE_BASEURL = "sqlite://"
        DATABASE_BASEURL = f"sqlite:///{_tempfile.name}"
    ELASTICSEARCH_URL = os.environ.get("KARP5_ELASTICSEARCH_TEST_URL") or "localhost:9201"
    OVERRIDE_ELASTICSEARCH_URL = True


@pytest.fixture(name="app", scope="session")
def fixture_app():
    app = create_app(TestConfig)

    assert TestConfig.OVERRIDE_ELASTICSEARCH_URL
    return app


# @pytest.fixture(scope="session")
# def real_app():
#     app = create_app()
#
#     return app


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


@pytest.fixture(name="cli_w_panacea", scope="session")
def fixture_cli_w_panacea(cli_w_es):
    r_create = cli_w_es.create_mode("panacea", "test")
    assert r_create.exit_code == 0

    r_publish = cli_w_es.publish_mode("panacea", "test")
    assert r_publish.exit_code == 0

    time.sleep(1)
    return cli_w_es


@pytest.fixture(name="cli_w_foo", scope="session")
def fixture_cli_w_foo(cli_w_es):
    r_create = cli_w_es.create_mode("foo", "test")
    assert r_create.exit_code == 0

    r_publish = cli_w_es.publish_mode("foo", "test")
    assert r_publish.exit_code == 0

    time.sleep(1)
    return cli_w_es


@pytest.fixture(name="app_w_auth", scope="session")
def fixture_app_w_auth(app):

    with auth_server.DummyAuthServer(conf_mgr, port=5001):
        yield app


@pytest.fixture(name="app_w_panacea", scope="session")
def fixture_app_w_panacea(app_w_auth, cli_w_panacea):
    if cli_w_panacea is None:
        pytest.skip()
    return app_w_auth


@pytest.fixture(scope="session")
def client_w_panacea(app_w_panacea):
    return app_w_panacea.test_client()


@pytest.fixture(name="app_w_foo", scope="session")
def fixture_app_w_foo(app_w_auth, cli_w_foo):
    if cli_w_foo is None:
        pytest.skip()
    return app_w_auth


@pytest.fixture(scope="session")
def client_w_foo(app_w_foo):
    return app_w_foo.test_client()
