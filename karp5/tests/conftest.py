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
assert os.environ["KARP5_INSTANCE_PATH"] == os.path.join(os.path.dirname(__file__), "data/")
print(os.environ["KARP5_INSTANCE_PATH"])

from karp5 import create_app  # noqa: E402
from karp5.cli import cli as karp5_cli, setup_cli  # noqa: E402
from karp5.config import conf_mgr  # noqa: E402

from karp5.tests._test_config import TestConfig


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


from karp5.tests.common_fixtures import (
    client,
    fixture_cli,
    fixture_cli_w_es,
    fixture_es,
)


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


@pytest.fixture(name="cli_w_large_lex", scope="session")
def fixture_cli_w_large_lex(cli_w_es):
    r_create = cli_w_es.create_mode("large_lex", "test")
    assert r_create.exit_code == 0

    r_publish = cli_w_es.publish_mode("large_lex", "test")
    assert r_publish.exit_code == 0

    time.sleep(1)
    return cli_w_es


@pytest.fixture(name="app_w_panacea", scope="session")
def fixture_app_w_panacea(app, cli_w_panacea):
    if cli_w_panacea is None:
        pytest.skip()
    return app


@pytest.fixture(scope="session")
def client_w_panacea(app_w_panacea):
    return app_w_panacea.test_client()


@pytest.fixture(name="app_w_foo", scope="session")
def fixture_app_w_foo(app, cli_w_foo):
    if cli_w_foo is None:
        pytest.skip()
    return app


@pytest.fixture(scope="session")
def client_w_foo(app_w_foo):
    return app_w_foo.test_client()


@pytest.fixture(name="app_w_large_lex", scope="session")
def fixture_app_w_large_lex(app, cli_w_large_lex):
    if cli_w_large_lex is None:
        pytest.skip()
    return app


@pytest.fixture(scope="session")
def client_w_large_lex(app_w_large_lex):
    return app_w_large_lex.test_client()
