# from karp5 import create_app

import karp5
from karp5.config import conf_mgr

# def test_config():
#     assert not create_app().testing


def test_config_testing(app):
    assert app.testing


def test_version(app):
    assert conf_mgr.version == karp5.__version__
