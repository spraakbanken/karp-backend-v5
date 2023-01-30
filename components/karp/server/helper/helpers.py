from flask import request
from json import loads
import logging
from karp.server import errorhandler as eh
from karp.server.helper import config_manager as configM
from urllib.parse import parse_qs


def get_user():
    auth = request.authorization
    return auth.username


def get_size(default=10, settings={}):
    from server.translator.parser import parse_extra
    query = request.query_string
    parsed = parse_qs(query)
    parse_extra(parsed, settings)
    return settings.get('size', default)


def get_querysettings(settings):
    from server.translator.parser import parse_extra
    query = request.query_string
    parsed = parse_qs(query)
    parse_extra(parsed, settings)


def check_lexiconName(lexicon, entry_lexicon, _id, action):
    if entry_lexicon != lexicon:
        msg = 'The entry does not belong in lexicon %s' % lexicon
        debug = ('Attemped to %s %s from %s, instead of %s'
                 % (action, _id, lexicon, entry_lexicon))
        raise eh.KarpElasticSearchError(msg, debug_msg=debug)


def get_update_index(lexicon, elastic, suggestion=False):
    index = ''
    try:
        if suggestion:
            index, typ = configM.get_lexicon_suggindex(lexicon)
        else:
            index, typ = configM.get_lexicon_index(lexicon)
        return elastic(lexicon=lexicon), index, typ

    except Exception as e:
        logging.exception(e)
        msg = "No writable mode for lexicon %s was found" % lexicon
        raise eh.KarpElasticSearchError(msg, debug_msg=msg+", index: "+index)


def read_data():
    """ Read the incoming data, make sure a message exists
        Raise errors if data is not well-formatted
    """
    try:
        request.get_data()
        data = loads(request.data)
    except ValueError as e:
        raise eh.KarpParsingError(str(e))
    if 'message' not in data:
        # fail if message is not there
        raise eh.KarpGeneralError('Input data not ok')
    if not data:
        errstr = "The source is empty. Empty documents not allowed"
        raise eh.KarpParsingError(errstr)
    return data
