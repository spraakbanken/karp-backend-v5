"""[summary]
"""
from karp5.errors import KarpException


class KarpConfigException(KarpException):
    """[summary]
    """

    def __init__(self, msg_fmt, *msg_args,  debug_msg=None):
        if not msg_args:
            msg = msg_fmt
        else:
            msg = msg_fmt % msg_args
        super().__init__(msg, debug_msg=debug_msg)
