# import this to start up the logging, always have this line at the top of the file
import logging

from flask import Flask
import pkg_resources

import six

# from .instance_info import get_instance_path

from .config import Config, get_instance_path


__version__ = '5.7.1'
__name = 'karp5'


def create_app(config_class = Config):
    app = Flask(__name, instance_path=get_instance_path())
    app.config.from_object(config_class)

    from app.search import bp as search_bp
    app.register_blueprint(search_bp)
    
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
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
# # import server.log
# from flask import Flask
#
# def create_app(app_path,
#                settings_override=None):
#     app = Flask('karp-backend', instance_path=app_path)
#
#     app.config.from_object('karp5.settings')
#     app.config.from_json('config/config.json', silent=True)
#     app.config.from_object(settings_override)
#
#     return app
#
# import logging
# logging.getLogger(__name__).addHandler(logging.NullHandler())