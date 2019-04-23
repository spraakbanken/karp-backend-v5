import functools
import logging


_logger = logging.getLogger('karp5')


def extra_src(*modes):
    def wrap(func):
        for mode in modes:
            func_name = func.__name__
            _logger.debug("Adding function '{}' to mode '{}'".format(func_name, mode))
    return wrap
