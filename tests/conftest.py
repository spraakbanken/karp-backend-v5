import pytest

# from karp_backend import create_app
import karp_backend.server.helper.flaskhelper as flaskhelper
import karp_backend.backend as backend


@pytest.fixture(scope="session")
def app():
    app = flaskhelper.app
    flaskhelper.register(backend.init)
    app.testing = True

    return app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
