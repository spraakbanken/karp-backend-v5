from __future__ import unicode_literals
import pytest

from app.config import Config
from app import create_app


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_URI = 'sqlite://'
    

@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()
