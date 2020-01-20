__version__ = "__version__ = '5.20.1'"

import pkg_resources
import logging
import logging.handlers
import os

import six

from .instance_info import get_instance_path

from flask import Flask, request

from karp5.config import Config, conf_mgr


__name = "karp5"


class RequestFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record):
        record.req_url = request.url
        record.req_remote_addr = request.remote_addr
        record.req_method = request.method
        return logging.Formatter.format(self, record)


def create_app(config_class=Config):
    app = Flask(__name, instance_path=get_instance_path())
    app.config.from_object(config_class)

    conf_mgr.app_config = config_class

    print("app.config = {}".format(app.config))

    # if app.config['ELASTICSEARCH_URL']:
    #     conf_mgr.override_elastic_url(app.config['ELASTICSEARCH_URL'])
    from karp5.context import auth

    if config_class.TESTING:
        auth.init("dummy")
    else:
        auth.init("std")

    from karp5.server.helper import flaskhelper

    flaskhelper.init_errorhandler(app)

    from karp5 import backend

    flaskhelper.register(app, backend.init)

    print("app.debug = {}".format(app.debug))
    print("app.testing = {}".format(app.testing))
    print("Setting up loggers")
    logger = logging.getLogger("karp5")
    logger.setLevel(app.config["LOG_LEVEL"])
    print("log_fmt = {}".format(app.config["LOG_FMT"]))
    print("log_datefmt = {}".format(app.config["LOG_DATEFMT"]))
    formatter = logging.Formatter(fmt=app.config["LOG_FMT"], datefmt=app.config["LOG_DATEFMT"])

    request_logger = logging.getLogger("karp5.requests")
    request_logger.setLevel(logging.INFO)
    request_formatter = RequestFormatter(
        fmt="[%(asctime)s] %(req_remote_addr)s %(req_method)s %(req_url)s %(message)s",
        datefmt=app.config["LOG_DATEFMT"],
    )
    if app.debug or app.config["LOG_TO_STDERR"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(app.config["LOG_LEVEL"])
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        request_stream_handler = logging.StreamHandler()
        request_stream_handler.setFormatter(request_formatter)
        request_logger.addHandler(request_stream_handler)
    else:
        log_dir = app.config["LOG_DIR"]
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "karp5.log"), when="d", interval=1, backupCount=0
        )
        file_handler.setLevel(app.config["LOG_LEVEL"])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        request_file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "karp5.requests.log"), when="d", interval=1, backupCount=0,
        )
        request_file_handler.setFormatter(request_formatter)
        request_logger.addHandler(request_file_handler)

    @app.after_request
    def after_request(response):
        """ Logging after every request. """
        request_logger.info(response.status)
        return response

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
