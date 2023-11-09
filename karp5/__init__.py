__version__ = "5.27.5"

import pkg_resources

import six

from karp5.config import conf_mgr
from karp5.presentation.server.app import create_app


__name = "karp5"


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
