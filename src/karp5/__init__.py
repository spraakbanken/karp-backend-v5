# import this to start up the logging, always have this line at the top of the file
import pkg_resources
import logging
import os

import six

from .instance_info import get_instance_path


from flask import Flask

from .config import Config


__version__ = "5.8.0"
__name = "karp5"


def create_app(config_class=Config):
    app = Flask(__name, instance_path=get_instance_path())
    app.config.from_object(config_class)

    print("app.config = {}".format(app.config))

    if app.config["ELASTICSEARCH_URL"]:
        from karp5.server.helper import configmanager

        configmanager.override_elastic_url(app.config["ELASTICSEARCH_URL"])

    from karp5.server.helper import flaskhelper

    flaskhelper.init_errorhandler(app)

    from karp5 import backend

    flaskhelper.register(app, backend.init)

    print("app.debug = {}".format(app.debug))
    print("app.testing = {}".format(app.testing))
    if not app.debug and not app.testing:
        logger = logging.getLogger("karp5")
        logger.setLevel(app.config["LOG_LEVEL"])
        formatter = logging.Formatter(
            fmt=app.config["LOG_FMT"], datefmt=app.config["LOG_DATEFMT"]
        )

        if app.config["LOG_TO_STDERR"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(app.config["LOG_LEVEL"])
            logger.addHandler(stream_handler)
        else:
            log_dir = app.config["LOG_DIR"]
            if not os.path.exists(log_dir):
                os.mkdir(log_dir)

            file_handler = logging.handlers.TimedRotatingFileHandler(
                os.path.join(log_dir, "karp5.log"), when="d", interval=1, backupCount=0
            )
            file_handler.setLevel(app.config["LOG_LEVEL"])
            logger.addHandler(file_handler)

    return app


def get_version():
    return __version__


def get_name():
    return __name


def get_pkg_resource(filename):
    assert pkg_resources.resource_exists(__name__, filename)
    result = pkg_resources.resource_string(__name__, filename)
    if isinstance(result, six.binary_type):
        result = result.decode("utf-8")
    return result
