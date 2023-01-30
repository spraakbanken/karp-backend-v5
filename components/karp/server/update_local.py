from flask import request, jsonify
from elasticsearch import helpers
from elasticsearch import exceptions as esExceptions
from . import errorhandler as eh
import config.setup as setupconf
from server.update import update_db, get_user, get_lexname
""" Methods for updating the database, including deletion and creation of indices
"""
sugg_index = setupconf.sugg_index
karp_index = setupconf.indexalias
_type = setupconf._type


def publish_index(index, elastic):
    """ Puts the alias of 'index' to be the main index (karp_index).
        Any other index will be removed from this alias.
    """
    try:
        ans = elastic.indices.update_aliases('{"actions" : [{"remove" : {"index":"*", "alias":"%s"}},{"add" : {"index": "%s", "alias": "%s"}}]}' % (index, karp_index, karp_index))
    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        raise eh.KarpElasticSearchError("Could not publish index", debug_msg=str(e))
    return jsonify(ans)


def publish_externalindex(index, elastic):
    """ Puts the alias of 'index' to be the main index (karp_index).
        Any other external index will be removed from this alias.
    """
    # remove any other index from the alias and then add the new index
    try:
        ans = elastic.indices.update_aliases('{"actions" : [{"remove" : {"index":"karpexternal*", "alias":"%s"}},{"add" : {"index": "%s", "alias": "%s"}}]}' % (index, karp_index, karp_index))
    except (esExceptions.RequestError, esExceptions.TransportError) as e:
        raise eh.KarpElasticSearchError("Could not publish index", debug_msg=str(e))
    return jsonify(ans)


# For uploading
def upload(informat, elastic, index='test', sql=False):
    """ Uploads the data to elastic and the database
        sql      if True,  the data will be stored in the SQL data base as well as ElasticSearch
                 if False, the data will only be stored in ElasticSearch
        informat can either be xml  - lmf
                               json - a single json object or a list of objects
                               bulk - a list of json objects annotated with index and type information,
                                      as accepted by ElasticSearch
        Requires the user to send their log in details
        Raises KarpElasticSearchError  if the data cannot be uploaded
        Raises KarpGeneralError        for other errors otherwise
    """

    # The actual parsing
    ok, err, data, names = parse_upload(informat, index=index, return_names=True)

    # Error handling on parsing
    if err:
        raise eh.KarpParsingError('\n'.join(err))

    # send to elastic and catch exceptions
    ok = 0
    try:  # trying to merge the two try:s will result in some errors sneaking past. don't know why.
        if sql:
            for res in helpers.streaming_bulk(elastic, data):
                _id = res[1].get('create').get('_id')  # res is a tuple, res[0]==True
                db_loaded, db_error = update_db(_id, data[ok].get('_source'), get_user(), 'entry automatically added or reloaded',
                                                data[ok].get('lexiconName'), status='imported')
                ok += db_loaded
                if db_error:
                    raise eh.KarpDbError(db_error)
        else:
            ok, err = helpers.bulk(elastic, data)
            if err:
                raise eh.KarpElasticSearchError("Error during upload. %s documents successfully uploaded. Message: %s.\n" % (ok, '\n'.join(err)))

    except helpers.BulkIndexError as e:
        # BulkIndexException is thrown for other parse errors
        # This exception has errors instead of error
        ok, err = ok, [er['create']['error'] for er in e.errors]
        raise eh.KarpElasticSearchError("Error during upload. %s documents successfully uploaded. Message: %s.\n" % (ok, '\n'.join(err)))

    except esExceptions.RequestError as e:
        # elasticsearch-py throws errors (TransportError) for invalid (empty) objects
        err = [e.error]
        raise eh.KarpElasticSearchError("Error during upload. %s documents successfully uploaded. Message: %s.\n" % (ok, '\n'.join(err)))

    except (SyntaxError, ValueError) as e:  # Parse error from xml
        err = [str(e)]
        raise eh.KarpParsingError('\n'.join(err))

    except Exception as e:
        err = ['Oops, an unpredicted error', str(e), '%s documents uploaded' % ok]
        raise eh.KarpGeneralError('\n'.join(err), '')

    if not ok:
        return "Warning. 0 documents uploaded\n" % ok
    return "Ok. %s documents uploaded\n" % ok


# For deleting lexicons
def delete_lexicon(index, lexicon, elastic, sql=False):
    """ Deletes a lexicon
        Requires the user to send their log in details
        Raises KarpElasticSearchError  if index is not found in the database
    """
    try:
        q = '{"query" : {"term" : {"lexiconName": "%s"}}}' % lexicon
        ans = elastic.delete_by_query(index=index, body=q)
        return jsonify(ans)
    except Exception as e:
        raise eh.KarpElasticSearchError("Could not delete index", debug_msg=str(e))


# For deleting indices
def delete_index(index, elastic):
    """ Deletes an index
        Requires the user to send their log in details
        Raises KarpElasticSearchError  if index is not found in the database
    """

    try:
        ans = elastic.indices.delete(index=index)
        return jsonify(ans)
    except Exception as e:
        raise eh.KarpElasticSearchError("Could not delete index", debug_msg=str(e))


# For creating indices
def create_index(index, elastic):
    """ Creates an index
        Requires the user to send their log in details
        Raises KarpElasticSearchError  if the index cannot be created
    """
    try:
        ans = elastic.indices.create(index=index)
        return jsonify(ans)
    except Exception as e:
        raise eh.KarpElasticSearchError('Could not create index, ' + str(e))


# For creating indices
def create_index_mapping(index, elastic):
    """ Creates an index and sets a given mapping to the index
        Requires the user to send their log in details
        Raises KarpElasticSearchError if the index cannot be created
    """
    request.get_data()   # need to call this method, in case the header does not specify the data type
    data = request.data  # from now on, the data is stored in request.data
    try:
        ans = elastic.indices.create(index=index, body=data)
        return jsonify(ans)
    except Exception as e:
        raise eh.KarpElasticSearchError("Could not create index", debug_msg=str(e))


# For getting the mapping
def get_mapping(index, elastic):
    """ Raises KarpElasticSearchError if the mapping cannot be found """
    try:
        ans = elastic.indices.get_mapping(index=index)
        return jsonify(ans)
    except Exception as e:
        raise eh.KarpElasticSearchError("Could not create index", debug_msg=str(e))


def parse_upload(informat, index='test', return_names=False):
    """ Parse the query and the post and put it into the desired json format
    """
    from .translator import bulkify as b

    request.get_data()   # need to call this method, in case the header does not specify the data type
    data = request.data  # from now on, the data is stored in request.data
    ok_formats = ["json"]  # ,"bulk","xml"]
    bulk_info = {'index': index, 'type': _type}
    ok, err, out_data = 0, [], []
    if informat not in ok_formats:
        # Show error if format is wrong
        return 0, ["Error: Format %s not recognized (should be one of %s)</p>" % (informat, ', '.join(ok_formats))], []

    try:
        if informat == "json":
            out_data = b.bulkify(data, bulk_info)

        if return_names:
            names = get_lexname(out_data)
    except SyntaxError as e:
        # Catch syntax errors from parsing with json.loads and xml
        ok, err = 0, [e.msg]

    except Exception as e:  # Parse error
        # This would probaly not be caught here, since
        # the xml parser returns an iterator
        ok, err = 0, ["%s not valid." % informat.title()]
    if return_names:
        return ok, err, out_data, names
    return ok, err, out_data
