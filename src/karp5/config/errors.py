"""[summary]
"""
from karp5.errors import KarpException


class KarpConfigException(KarpException):
    """[summary]
    """

    def __init__(self, message, debug_msg=None):
        Exception.__init__(self)
        KarpException.__init__(self, message, debug_msg=(debug_msg or message))
