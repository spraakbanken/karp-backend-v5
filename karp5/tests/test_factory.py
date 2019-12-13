
from karp5 import create_app


# def test_config():
#     assert not create_app().testing


def test_config_testing(app):
    assert app.testing
