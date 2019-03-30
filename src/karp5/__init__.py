# import this to start up the logging, always have this line at the top of the file
import pkg_resources
import logging
import six

from .instance_info import get_instance_path



from flask import Flask

from .config import Config


__version__ = '5.8.0'
__name = 'karp5'


def create_app(config_class = Config):
    app = Flask(__name, instance_path=get_instance_path())
    app.config.from_object(config_class)

    return app


def get_version():
    return __version__


def get_name():
    return __name


def get_pkg_resource(filename):
    assert pkg_resources.resource_exists(__name__, filename)
    result = pkg_resources.resource_string(__name__, filename)
    if isinstance(result, six.binary_type):
        result = result.decode('utf-8')
    return result
