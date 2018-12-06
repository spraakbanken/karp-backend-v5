from elasticsearch import exceptions as esExceptions
import karp_backend.server.errorhandler as eh
from karp_backend.dbhandler.dbhandler import dbselect
from flask import request, jsonify
from json import loads
import logging
from karp_backend.server.auth import validate_user
import karp_backend.server.helper.helpers as helpers
import karp_backend.server.helper.configmanager as configM
import karp_backend.server.update as update


def suggest(lexicon, _id):
    return update.add_doc(lexicon, _id=_id, suggestion=True)


def checksuggestions():
    auth, permitted = validate_user()
    settings = {'allowed': permitted}
    helpers.get_querysettings(settings)
    size = settings.get('size', 50)
    lexicons = settings.get('resource', [])
    status = settings.get('status', ['waiting', 'rejected', 'accepted'])
    logging.debug('checksuggestions in %s' % lexicons)
    if not lexicons:
        return jsonify({'updates': []})
    updates = []
    for lexicon in lexicons:
        # add updates from lexicons that are kept in sql
        if configM.get_lexicon_sql(lexicon):
            updates.extend(dbselect(lexicon, suggestion=True, status=status,
                                    max_hits=size))

    return jsonify({'updates': updates})


def acceptsuggestion(lexicon, _id):
    try:
        ans = savesuggestion(lexicon, _id)
        logging.debug('saved sugg')
        return jsonify(ans)
    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        update.handle_update_error(e, {"id": _id}, helpers.get_user(), 'accept')
        raise eh.KarpElasticSearchError("Error during update. Document not saved.",
                                        debug_msg=str(e))
    except Exception as e:
        update.handle_update_error(e, {"id": _id}, helpers.get_user(), 'accept')
        raise eh.KarpGeneralError(str(e))


def acceptmodified(lexicon, _id):
    try:
        request.get_data()
        data = loads(request.data)
        modified_doc = data
        ans = savesuggestion(lexicon, _id,
                             status='accepted_modified',
                             source=modified_doc)
        return jsonify(ans)
    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        logging.exception(e)
        update.handle_update_error(e, {"id": _id, "data": data},
                                   helpers.get_user(), 'accept modified')
        raise eh.KarpElasticSearchError("Error during update. Document not saved.",
                                        debug_msg=str(e))
    except Exception as e:
        logging.exception(e)
        update.handle_update_error(e, {"id": _id, "data": data},
                                   helpers.get_user(), 'accept modified')
        raise eh.KarpGeneralError(str(e))


def savesuggestion(lexicon, _id, status='accepted', source=''):
    sugg_index, typ = configM.get_lexicon_suggindex(lexicon)
    es = configM.elastic(lexicon=lexicon)
    suggestion = es.get(index=sugg_index, doc_type=typ, id=_id)
    auth, permitted = validate_user()
    set_lexicon = suggestion["_source"]["lexiconName"]
    helpers.check_lexiconName(lexicon, set_lexicon, 'rejectsuggestion', _id)
    if lexicon not in permitted:
        raise eh.KarpAuthenticationError('You are not allowed to update lexicon %s'
                                         % lexicon)

    origin = dbselect(lexicon, suggestion=True, _id=_id, max_hits=1)[0]
    origid = origin['origid']
    request.get_data()
    data = loads(request.data)
    message = data.get('message')
    suggestion['message'] = message
    suggestion['version'] = origin['version']
    if not source:
        source = suggestion
    # the user log in is checked in add_doc
    # add_doc raises exception if ES
    if origid:
        # update in ES
        ans = update.update_doc(lexicon, origid, data=source, live=False)
    else:
        # add to ES
        ans = update.add_doc(lexicon, live=False, data=source)
        origid = ans.get('_id')
    # mark as accepted
    ok, err = update.modify_db(_id, lexicon, message, status, origid=origid)
    # delete from suggestion index
    suggans = update.delete_entry(lexicon, _id, sql=False, live=False,
                                  suggestion=True)
    ans['sugg_db_loaded'] = ok
    ans['sugg_es_ans'] = suggans
    if not ok:
        logging.debug(err)
    update.send_notification(origin['user'], message, _id, status)
    return ans


def rejectsuggestion(lexicon, _id):
    try:
        origin = dbselect(lexicon, suggestion=True, _id=_id, max_hits=1)[0]
    except Exception as e:
        # if error occurs here, the suggestion is not in sql
        raise eh.KarpDbError('Rejection not found',
                             'Rejection not found: %s' % str(e))
    auth, permitted = validate_user()
    set_lexicon = origin["doc"]["lexiconName"]
    helpers.check_lexiconName(lexicon, set_lexicon, 'rejectsuggestion', _id)
    if lexicon not in permitted:
        raise eh.KarpAuthenticationError('You are not allowed to update lexicon %s'
                                         % lexicon)
    try:
        origin = dbselect(lexicon, suggestion=True, _id=_id, max_hits=1)[0]
        # delete from suggestion index
        # the user log in is checked in delete_entry
        # delete_entry raises exception if ES fails
        sugg_index, typ = configM.get_lexicon_suggindex(lexicon)

        ans = update.delete_entry(lexicon, _id, sql=False, live=False,
                                  suggestion=True)
        request.get_data()
        data = loads(request.data)
        message = data.get('message')
        # mark as rejected
        ok, err = update.modify_db(_id, lexicon, message, "rejected")

        ans['sugg_db_loaded'] = ok
        if not ok:
            logging.debug(err)
        update.send_notification(origin['user'], message, _id, "rejected")
        return jsonify(ans)
    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        update.handle_update_error(e, {"id": _id}, helpers.get_user(), 'reject')
        raise eh.KarpElasticSearchError("Error during update. Document not saved.",
                                        debug_msg=str(e))
    except Exception as e:
        update.handle_update_error(e, {"id": _id}, helpers.get_user(), 'reject')
        raise eh.KarpGeneralError(str(e))


def checksuggestion(lexicon, _id):
    # TODO add exception handling
    try:
        return jsonify({'updates': dbselect(lexicon, suggestion=True,
                        _id=_id, max_hits=1)})
    except Exception as e:
        raise eh.KarpGeneralError(str(e))
