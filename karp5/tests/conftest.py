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
os.environ["KARP5_INSTANCE_PATH"] = os.path.join(os.path.dirname(__file__), "data/")

from karp5 import create_app, Config  # noqa: E402
from karp5.cli import cli as karp5_cli, setup_cli  # noqa: E402
from karp5.config import conf_mgr  # noqa: E402

from karp5.tests._test_config import TestConfig  # pytype: disable=import-error


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


from karp5.tests.common_fixtures import (  # pytype: disable=import-error
    fixture_client,
    fixture_cli,
    fixture_cli_w_es,
    fixture_es,
)  # pytype: disable=import-error


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
    from tests import auth_server

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
