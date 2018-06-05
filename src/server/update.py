""" Methods for updating the database,
    including deletion and creation of indices
"""
import datetime
import logging
from elasticsearch import helpers as eshelpers
from elasticsearch import exceptions as esExceptions
from flask import request, jsonify
from json import dumps
import src.server.errorhandler as eh
import src.server.helper.configmanager as configM
import src.server.auth as auth
import src.server.helper.helpers as helpers
import src.server.translator.validatejson as validate
from src.server.autoupdates import auto_update_document, autoupdate_child



def checkuser():
    """ Shows which lexica the user may edit """
    authdict, permitted = auth.validate_user(mode="verbose")
    return jsonify(permitted)


def delete_entry(lexicon, _id, sql=False, live=True, suggestion=False):
    # delete by id
    try:
        msg = request.args.get('message', ['removed'])
        es, index, typ = helpers.get_update_index(lexicon, suggestion=suggestion)
        ans_entry = es.get(index=index, doc_type=typ, id=_id)
        lexiconName = ans_entry['_source']['lexiconName']
        helpers.check_lexiconName(lexicon, lexiconName, _id, 'delete')

        authdict, permitted = auth.validate_user()
        if lexiconName not in permitted:
            raise eh.KarpAuthenticationError('You are not allowed to modify '
                                             'the lexicon %s, only %s'
                                             % (lexiconName, permitted))

        # doc_type must be set
        ans = es.delete(index=index, doc_type=typ, id=_id)
        db_loaded, db_error = 0, ''
        if sql:
            # logging.debug("Delete " + msg)
            logging.debug('delete from sql.\nmsg %s\nans_entry %s',
                          msg, ans_entry)
            db_loaded, db_error = update_db(_id, ans_entry['_source'],
                                            helpers.get_user(), msg,
                                            lexiconName, status='removed')
            logging.debug('updated db %s %s', db_loaded, db_error)

        if db_error:
            raise eh.KarpDbError(db_error)

    except eshelpers.BulkIndexError as e:
        # BulkIndexException is thrown for other parse errors
        # This exception has errors instead of error
        handle_update_error(e, {"id": _id}, helpers.get_user(), 'delete')
        err = [er['create']['error'] for er in e.errors]
        raise eh.KarpElasticSearchError("Error during deletion %s.\n"
                                        % '\n'.join(err))

    except (esExceptions.TransportError, esExceptions.RequestError) as e:
        # elasticsearch-py throws errors (TransportError)
        # for invalid (empty) objects
        handle_update_error(e, {"id": _id}, helpers.get_user(), 'delete')
        err = [e.error]
        raise eh.KarpElasticSearchError('Error during deletion. '
                                        'Message: %s.\n'
                                        % '\n'.join(err))

    except Exception as e:
        handle_update_error(e, {"id": _id}, helpers.get_user(), 'delete')
        err = ['Oops, an unpredicted error', str(e),
               'Document not deleted']
        raise eh.KarpGeneralError('Document not deleted',
                                  debug_msg=' '.join(err))

    jsonans = {'es_loaded': 1, 'sql_loaded': db_loaded, 'es_ans': ans}
    if db_error:
        logging.debug(db_error)
    if live:
        return jsonify(jsonans)
    else:
        return jsonans


def get_lexname(data):
    names = set()
    for item in data:
        names.add(item['_source']['lexiconName'])
    return names


def update_doc(lexicon, _id, data=None, live=True):
    """ Updates a posted document in the index 'index' with type 'typ'.
        The document must contain a field called 'doc' with
        the information to be sent.
        The fields 'version' and 'message' are optional.
    """
    # send user name and password,
    # {'doc' : es_doc, 'version' : last version, 'message' : update message}
    authdict, permitted = auth.validate_user()

    if data is None:
        data = helpers.read_data()

    try:
        index, typ = configM.get_lexicon_index(lexicon)
        es = configM.elastic(lexicon=lexicon)
        origin = es.get(index=index, doc_type=typ, id=_id)
    except Exception as e:
        logging.warning("Looking for entry at the wrong place:")
        logging.exception(e)
        msg = "The entry %s in lexicon %s was not found" % (_id, lexicon)
        raise eh.KarpElasticSearchError(msg, debug_msg=msg+" in index "+index)

    lexiconName = origin['_source']['lexiconName']
    helpers.check_lexiconName(lexicon, lexiconName, _id, 'update')
    data_doc = data.get('doc') or data.get('_source')
    version = data.get('version')
    msg = data["message"]

    if lexicon not in permitted:
        raise eh.KarpAuthenticationError('You are not allowed to modify the '
                                         'lexicon %s, only %s'
                                         % (lexicon, permitted),
                                         status_code=403)

    validate.validate_json(data_doc, lexicon)
    date = datetime.datetime.now()
    user = helpers.get_user()
    auto_update_document(data_doc, lexicon, 'update', user, date)
    try:
        if version is not None and version != -1:
            ans = es.index(index=index, doc_type=typ, id=_id, version=version,
                           body=data_doc, op_type='index')
        else:
            ans = es.index(index=index, doc_type=typ, id=_id,
                           body=data_doc, op_type='index')

    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        # Transport error might be version conflict
        logging.exception(e)
        logging.debug('index: %s, type: %s, id: %s', index, typ, _id)
        handle_update_error(e, {"id": _id, "data": data}, user, 'update')
        raise eh.KarpElasticSearchError("Error during update. Message: %s.\n"
                                        % str(e))
    except Exception as e:
        handle_update_error(e, {"id": _id, "data": data}, user, 'update')
        raise eh.KarpElasticSearchError("Unexpected error during update.")

    db_loaded, db_error = update_db(_id, data_doc, user, msg, lexiconName,
                                    status='changed', date=date,
                                    version=ans.get('_version', version))

    jsonans = {'es_loaded': 1, 'sql_loaded': db_loaded, 'es_ans': ans}
    if db_error:
        logging.debug(db_error)
    if live:
        return jsonify(jsonans)
    else:
        return jsonans


def update_db(_id, doc, user, msg, lex, status='', version='', suggestion='',
              date=''):
    """ Inserts the document doc into the sql data base, using its id and
        the current date and time as a key. The user name and a messange is
        also saved.
        Returns a tuple (loaded, error), where 'loaded' is 1 if the operation
        succeeded and 0 otherwise and 'error' is the error message given, if
        any.
    """
    from src.dbhandler.dbhandler import update
    return update(_id, dumps(doc), user, msg, lex, status=status,
                  version=version, suggestion_id=suggestion, date=date)


def modify_db(_id, lexicon, msg, status, origid=''):
    """ Updates a document in the suggestion sql data base, using its id.
        Returns a tuple (loaded, error), where 'loaded' is 1 if the operation
        succeeded and 0 otherwise and 'error' is the error message given, if
        any.
    """
    from src.dbhandler.dbhandler import modifysuggestion
    return modifysuggestion(_id, lexicon, msg=msg, status=status, origid=origid)


def add_multi_doc(lexicon, index=''):
    import src.dbhandler.dbhandler as db

    data = helpers.read_data()
    documents = data.get('doc', '') or data.get('_source')
    message = data['message']
    es, index, typ = helpers.get_update_index(lexicon)
    # validate that the user may update the lexica
    authdict, permitted = auth.validate_user()
    if lexicon not in permitted:
        errstr = 'You are not allowed to modify the lexicon %s'
        raise eh.KarpAuthenticationError(errstr % lexicon,
                                         status_code=403)
    user = helpers.get_user()
    try:
        bulk, sql_bulk, ids = [], [], []
        ok = 0
        for doc in documents:
            doc['lexiconName'] = lexicon
            validate.validate_json(doc, lexicon)
            date = datetime.datetime.now()
            logging.debug('\n\nWill go to autoupdate\n\n')
            auto_update_document(doc, lexicon, 'add', user, date)
            bulk.append({'_index': index, '_type': typ, '_source': doc})

        for ix, res in enumerate(eshelpers.streaming_bulk(es, bulk)):
            _id = res[1].get('index').get('_id')
            source = bulk[ix].get('_source')
            if isinstance(source, dict):
                source = dumps(source)
            sql_bulk.append((_id, source, user, 'multi add - %s' % message,
                             lexicon, 'imported'))
            ids.append(_id)
            ok += 1

    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        handle_update_error(e, data, user, 'add')
        raise eh.KarpElasticSearchError("Error during update. Message: %s.\n"
                                        % str(e))

    db_loaded, db_error = db.update_bulk(lexicon, sql_bulk)
    if db_error:
        logging.debug(db_error)

    jsonans = {'es_loaded': ok, 'sql_loaded': db_loaded, 'suggestion': False,
               'ids': ids}
    return jsonify(jsonans)


def add_doc(lexicon, index='', _id=None, suggestion=False, data=None,
            live=True):
    """ Adds an entry to the index 'index' with type 'typ' in ES and sql.
        The post data must contain a field called 'doc' with the information to
        be sent.
        The fields 'version' and 'message' are optional.
    """
    if data is None or not data:
        data = helpers.read_data()

    data_doc = data.get('doc', '') or data.get('_source')
    message = data['message']
    version = data.get('version', -1)
    es, index, typ = helpers.get_update_index(lexicon, suggestion=suggestion)
    lexiconName = lexicon or data_doc.get("lexiconName", '')
    helpers.check_lexiconName(lexicon, lexiconName, 'add', _id)

    # lexiconOrder = data_doc.get("lexiconOrder", None)
    if not lexiconName:
        raise eh.KarpParsingError("The field lexiconName is empty, "
                                  "although it is required.")

    if suggestion:
        orgin_id = _id or True  # save as reference in db
        _id = ''  # add as new to the suggestion index
        status = 'waiting'
        user = data['user']
    else:
        # validate that the user may update the lexica
        authdict, permitted = auth.validate_user()
        if lexiconName not in permitted:
            errstr = 'You are not allowed to modify the lexicon %s'
            raise eh.KarpAuthenticationError(errstr % lexiconName,
                                             status_code=403)

        orgin_id = ''  # not a suggestion
        user = helpers.get_user()
        status = 'added'
    try:
        validate.validate_json(data_doc, lexicon)

        date = datetime.datetime.now()
        auto_update_document(data_doc, lexiconName, 'add', user, date)
        ans = es.index(index=index, doc_type=typ, body=data_doc, id=_id)
        _id = ans.get('_id')
        version = ans.get('_version', -1)
        db_loaded, db_error = update_db(_id, data_doc, user, message,
                                        lexiconName, version=version,
                                        suggestion=orgin_id, status=status,
                                        date=date)

    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        handle_update_error(e, data, user, 'add')
        raise eh.KarpElasticSearchError("Error during update. Message: %s.\n"
                                        % str(e))
    except Exception as e:
        raise eh.KarpGeneralError(str(e))

    jsonans = {'es_loaded': 1, 'sql_loaded': db_loaded, 'es_ans': ans,
               'suggestion': suggestion, 'id': _id}
    if db_error:
        logging.debug(db_error)
    if live:
        return jsonify(jsonans)
    else:
        return jsonans


def add_child(lexicon, parentid, suggestion=False):

    es, index, typ = helpers.get_update_index(lexicon, suggestion=suggestion)
    parent = es.get(index=index, doc_type=typ, id=parentid).get("_source")

    data = helpers.read_data()
    data_doc = data.get('doc', '') or data.get('_source')
    msg = data["message"]
    user = helpers.get_user()

    # add child to parent
    autoupdate_child(data_doc, parent, lexicon, user, '')
    parent_doc = {"doc": parent, "user": user, "message": msg}
    logging.debug('save parent %s', parent_doc)
    logging.debug('save child %s', parent_doc)
    parres = update_doc(lexicon, parentid, data=parent_doc, live=False)
    # add child to lexicon
    childres = add_doc(lexicon, index=index, data=data, live=False)
    return jsonify({"parent": parres, "child": childres})


def handle_update_error(error, data, user, action):
    """ Sends emails to admins about updates that failed
    """
    from src.dbhandler.dbhandler import handle_error
    return handle_error(error, user, "Action: " + action, data)


def send_notification(user, message, _id, status):
    import re
    if re.match('^[^@]+@[^@]+\.[^@]+$', user):
        import src.dbhandler.emailsender as sender
        msg = 'Your suggestion with id %s has been %s with the message:\n"%s"'\
              % (_id, status, message)
        subject = 'Karp: The status of your suggestion has been changed'
        sender.send_notification(user, subject, msg)
