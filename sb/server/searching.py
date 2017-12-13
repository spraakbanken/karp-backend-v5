from flask import request, jsonify
from json import loads
import logging
import src.server.errorhandler as Err
import src.server.helper.configmanager as configM
from src.server.translator import parsererror as PErr
from src.server.translator import fieldmapping as F
import src.server.translator.parser as parser
from src.server.auth import validate_user


def saldopath(elastic):
    try:
        query = request.args['q']
    except Exception as e:
        raise Err.KarpQueryError('Parse error, no query given', user_msg='Parse error',
                                 debug_msg=e.message, query='')
    try:
        # TODO don't construct this here!
        auth, permitted = validate_user(mode="read")
        mode = 'saldo'
        settings = {"allowed": permitted, "mode": mode}
        search_q = 'q=extended||and|sense.search|equals|%s&resource=saldo'
        elasticq = parser.parse((search_q % query).encode('utf8'), settings=settings)
        index, typ = configM.get_mode_index(mode)
        ans = elastic.search(index=index, body=loads(elasticq))
        chain = [get_sense(ans)]
        parent = get_primary(ans)
        # saldo paths are never deeper than 16, put a max limit to the number
        # of loop iterations
        depth = 0
        while parent and depth < 30:
            # hackhack, no need to parse again
            elasticq = parser.parse((search_q % parent).encode('utf8'),
                                    settings=settings)
            ans = elastic.search(index=index, body=loads(elasticq))
            chain += [get_sense(ans)]
            parent = get_primary(ans)
            depth += 1

        return jsonify({"path": chain})

    except PErr.QueryError as e:
        logging.debug(str(e))
        raise Err.KarpQueryError('Parse error', user_msg='Parse error',
                                 debug_msg=e.message, query=query)

    except Err.KarpQueryError as e:
        logging.exception(e)
        msg = e.user_msg % query
        raise Err.KarpQueryError(msg, user_msg=msg, debug_msg=e.debug_msg,
                                 query=query)
    except Exception as e:
        # TODO only catch relevant exceptions
        logging.exception(e)
        raise Err.KarpGeneralError('Unknown error', debug_msg=e.message,
                                   query=query)


def get_sense(ans):
    try:
        for s in ans.get('hits').get('hits')[0]['_source'].get('Sense'):
            # there will only be one sense in saldo
            return s.get('senseid')
        return ''
    except Exception as e:
        msg = 'Sense "%s" not found in Saldo'
        raise Err.KarpQueryError(msg, user_msg=msg, debug_msg=e.message)


def get_primary(ans):
    for s in ans.get('hits').get('hits')[0]['_source'].get('Sense'):
        # there will only be one sense in saldo
        return s.get('SenseRelations', {}).get('primary', '')
    return ''


def autocomplete(mode, boost, q):
    """ Constructs an autocompletion query, searching for lemgrams starting
        with 'text'
        Returns a query object to be sent to elastic search
    """
    # external mode: exclude msd tags that mark compounds
    # q should be equal to baseform or be equal to an inflected form which does
    # not have the msd tag ci, cm och sms
    exp = '''"nested" : {"path" :"WordForms", "query" : {"function_score": {%s,
             "query" : { "bool" : {"should" :
             [{"match_phrase" : {"%s" : "%s"}}, {"bool" :
               {"must" : [{"match_phrase" : {"%s" : "%s"}},
               {"bool" : {"must_not" : [{"regexp" : {"WordForms.msd" :
                "c|ci|cm|sms"}}]}}]}}]}}}}}'''
    return exp % (boost, F.lookup("baseform", mode), q,
                  F.lookup("wf_inflected", mode), q)
