# import functools
import logging

from karp5.config import mgr as conf_mgr


_logger = logging.getLogger("karp5")


def extra_src(*modes):
    def decorate(func):
        for mode in modes:
            _logger.debug(
                "Adding function '{}' to mode '{}'".format(func.__name__, mode)
            )
            conf_mgr.add_extra_src(mode, func)
        return func

    return decorate
