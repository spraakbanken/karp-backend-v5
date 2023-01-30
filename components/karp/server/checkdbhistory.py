from flask import jsonify
import logging
from karp.server import errorhandler as eh
from karp.server.helper import config_manager as configM
from karp.server.helper import helpers
from karp.server.auth import validate_user


def checkhistory(lexicon, lid):
    """ Shows the update log of an entry """
    from dbhandler.dbhandler import dbselect
    auth, permitted = validate_user(mode="read")
    settings = {'allowed': permitted}
    size = helpers.get_size(default=10, settings=settings)
    return jsonify({'updates': dbselect(lexicon, _id=lid, max_hits=size)})


def checkuserhistory():
    """ Shows the updates a user has made """
    try:
        auth, permitted = validate_user()
        user = helpers.get_user()
    except AttributeError:
        raise eh.KarpGeneralError('No user name provided', 'checkuserhistory')
    try:
        size = helpers.get_size(default=10, settings={'allowed': permitted})
        from dbhandler.dbhandler import dbselect
        updates = []
        for lexicon in permitted:
            # add updates from lexicons that are kept in sql
            if configM.get_lexicon_sql(lexicon):
                updates.extend(dbselect(lexicon, user=user, max_hits=size))

        return jsonify({'updates': updates})
    except Exception as e:
        logging.exception(e)
        raise eh.KarpGeneralError(str(e))


def checklexiconhistory(lexicon, date):
    """ Shows the updates on one lexicon """
    try:
        auth, permitted = validate_user()
        if lexicon not in permitted:
            raise eh.KarpAuthenticationError('You are not allowed to update lexicon %s' % lexicon)
        settings = {"allowed": permitted}
        helpers.get_querysettings(settings)
        size = settings.get('size', 10)
        status = settings.get('status', ['added', 'changed', 'removed'])

        from dbhandler.dbhandler import dbselect
        return jsonify({'resource': lexicon,
                        'updates': dbselect(lexicon, status=status,
                                            from_date=date, max_hits=size)})
    except Exception as e:
        raise eh.KarpGeneralError(str(e))


def comparejson(lexicon, _id, fromdate='', todate=''):
    from dbhandler.dbhandler import dbselect
    import server.translator.jsondiff
    auth, permitted = validate_user()
    if lexicon not in permitted:
        raise eh.KarpAuthenticationError('You are not allowed to update')

    try:
        if not todate:
            import datetime
            todate = datetime.datetime.now()
            tojson = dbselect(lexicon, max_hits=1, to_date=todate, _id=_id)[0]
        else:
            tojson = dbselect(lexicon, exact_date=todate, _id=_id)[0]

    # TODO catch the error here and print it to the log.
    # It is probably not really sql that raises the exception
    except Exception:
        raise eh.KarpDbError('Could not find any entry from %s' % todate)

    try:
        if not fromdate:
            jsons = dbselect(lexicon, max_hits=2, to_date=todate, _id=_id)
            fromjson = {'doc': {}} if len(jsons) == 1 else jsons[1]
        else:
            fromjson = dbselect(lexicon, exact_date=fromdate, _id=_id)[0]

        fromjson = fromjson['doc']
        tojson = tojson['doc']
    # TODO catch the error here and print it to the log.
    # It is probably not really sql that raises the exception
    except Exception:
        raise eh.KarpDbError('Could not find any entry from %s' % fromdate)
    return jsonify({'diff': server.translator.jsondiff.compare(fromjson,
                                                               tojson)})
