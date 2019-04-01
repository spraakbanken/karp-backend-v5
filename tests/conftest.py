import pytest

import dotenv
dotenv.load_dotenv(dotenv_path='.env', verbose=True)

from karp5 import create_app, Config

class TestConfig(Config):
    TESTING = True

@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)

    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
