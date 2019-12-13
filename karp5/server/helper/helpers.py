
from builtins import str
from flask import request
from json import loads
import logging
from karp5 import errors
from karp5.config import mgr as conf_mgr


_logger = logging.getLogger("karp5")


def get_user():
    auth = request.authorization
    if auth is None:
        return "UnkownUser"
    return auth.username


def get_size(default=10, settings={}):
    from karp5.server.translator.parser import parse_extra

    parse_extra(settings)
    return settings.get("size", default)


def get_querysettings(settings):
    from karp5.server.translator.parser import parse_extra

    parse_extra(settings)


def check_lexiconName(lexicon, entry_lexicon, _id, action):
    if entry_lexicon != lexicon:
        msg = "The entry does not belong in lexicon %s" % lexicon
        debug = "Attemped to %s %s from %s, instead of %s" % (
            action,
            _id,
            lexicon,
            entry_lexicon,
        )
        raise errors.KarpElasticSearchError(msg, debug_msg=debug)


def get_update_index(lexicon, suggestion=False):
    index = ""
    try:
        if suggestion:
            index, typ = conf_mgr.get_lexicon_suggindex(lexicon)
        else:
            index, typ = conf_mgr.get_lexicon_index(lexicon)
        return conf_mgr.elastic(lexicon=lexicon), index, typ

    except Exception as e:
        _logger.exception(e)
        msg = "No writable mode for lexicon %s was found" % lexicon
        raise errors.KarpElasticSearchError(msg, debug_msg=msg + ", index: " + index)


def read_data():
    """ Read the incoming data, make sure a message exists
        Raise errors if data is not well-formatted
    """
    try:
        request.get_data()
        data = loads(request.data)
    except ValueError as e:
        raise errors.KarpParsingError(str(e))
    if "message" not in data:
        # fail if message is not there
        raise errors.KarpGeneralError("Input data not ok")
    if not data:
        errstr = "The source is empty. Empty documents not allowed"
        raise errors.KarpParsingError(errstr)
    return data


def notdefined(msg):
    def f(*args, **kwargs):
        raise errors.KarpQueryError(msg)

    return f
