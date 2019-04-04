import pytest

import dotenv
dotenv.load_dotenv(dotenv_path='.env', verbose=True)

# from karp5 import create_app
import karp5.server.helper.flaskhelper as flaskhelper
import karp5.backend as backend


@pytest.fixture(scope="session")
def app():
    app = flaskhelper.app
    flaskhelper.register(backend.init)
    app.testing = True

    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
