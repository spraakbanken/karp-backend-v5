from flask import jsonify, Flask, request
import json
import os
from multiprocessing import Process

from karp5.config import conf_mgr


def create_app(mgr):
    app = Flask("Testing auth server")
    app.conf_mgr = conf_mgr

    @app.route("/")
    def index():
        return "I am a testing authentication server\n"

    @app.route("/resources", methods=["GET", "POST"])
    @app.route("/authenticate", methods=["GET", "POST"])
    def resources():
        lexlist = {}

        for name, val in app.conf_mgr.lexicons.items():
            lexlist[name] = {"read": True, "write": True, "admin": True}

        print("lexlist = {}".format(lexlist))

        return jsonify(
            {
                "permitted_resources": {"lexica": lexlist},
                "username": "test_user",
                "authenticated": True,
            }
        )

    return app


def run_app(mgr, port=8082):
    print("Starting auth server on port {port}".format(port=port))
    app = create_app(mgr)
    app.run(port=port, host="0.0.0.0")


class DummyAuthServer:
    def __init__(self, mgr, port=8082):
        self.port = port
        self.conf_mgr = mgr

        self.process = None
        self.started = False

    def start(self, block=True):
        self.process = Process(target=run_app, args=(self.conf_mgr, self.port))
        self.process.start()
        self.started = True

    def stop(self):
        self.started = False
        if self.process:
            self.process.terminate()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()
