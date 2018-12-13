#!/usr/bin/python2
import json
import sys
import os

import six

from elasticsearch import helpers as es_helpers
from elasticsearch import exceptions as esExceptions

import karp_backend.dbhandler.dbhandler as db
import karp_backend.server.helper.configmanager as configM
from karp_backend.util import json_iter
from karp_backend import document


def get_mapping(index):
    filepath = 'config/mappings/mappingconf_%s.json' % index
    try:
        return open(filepath).read()
    except:
        return None


def make_indexname(index, suffix):
    return index+'_'+suffix


def name_new_index():
    import datetime
    date = datetime.datetime.now().strftime('%Y%m%d')
    return 'karp' + date


def upload(informat, name, order, data, elastic, index, typ, sql=False,
           verbose=True, with_id=False):
    """ Uploads the data to elastic and the database
        sql      if True,  the data will be stored in the SQL database as well
                 as ElasticSearch
                 if False, the data will only be stored in ElasticSearch
        informat can either be xml  - lmf
                               json - a single json object or a list of objects
                               bulk - a list of json objects annotated with
                                      index and type information, as accepted
                                      by ElasticSearch
    """
    try:
        # The actual parsing
        data = parse_upload(informat, name, order, data, index, typ,
                            with_id=with_id)
    except Exception:
        print('Error while reading data from %s' % name)
        raise

    ok = 0
    if sql:
        # stream entries one by one to elastic, then update sql db
        # streaming_bulk will notify us at once when an entry fails
        sql_bulk = []
        for res in es_helpers.streaming_bulk(elastic, data, request_timeout=60):
            # res is a tuple, res[0]==True
            ansname = 'index' # if with_id else 'create' -- changed from ES2
            _id = res[1].get(ansname).get('_id')
            data_doc = data[ok].get('_source')
            if not isinstance(data_doc, dict):
                data_doc = json.loads(data_doc)
            sql_doc = document.doc_to_sql(data_doc, data_doc['lexiconName'], 'bulk')
            sql_bulk.append((_id, json.dumps(sql_doc), 'admin',
                             'entry automatically added or reloaded', name,
                             'imported'))
            ok += 1
        db_loaded, db_error = db.update_bulk(name, sql_bulk)
        if db_error:
            raise Exception(db_error)
        ok += db_loaded
    else:
        # upload all at once to elastic
        ok, err = es_helpers.bulk(elastic, data, request_timeout=60)
        if err:
            msg = "Error during upload. %s documents successfully uploaded. \
                   Message: %s.\n"
            raise Exception(msg % (ok, '\n'.join(err)))
    if not ok:
        raise Exception("No data")
        print >> sys.stderr, "Warning. 0 documents uploaded\n"
    if verbose:
        print("Ok. %s documents uploaded\n" % ok)


def parse_upload(informat, lexname, lexorder, data, index, typ, with_id=False):
    """ Parse the query and the post and put it into the desired json format
    """
    import karp_backend.server.translator.bulkify as b

    bulk_info = {'index': index, 'type': typ}
    out_data = 0, [], []

    if informat == "json":
        out_data = b.bulkify(data, bulk_info, with_id=with_id)
    else:
        raise "Don't know how to parse %s" % informat

    return out_data


def recover(alias, suffix, lexicon, create_new=True):
    # TODO test this
    """ Recovers the data to ES, uses SQL as the trusted base version.
        Find the last version of every SQL entry and send this to ES.
    """
    import karp_backend.server.translator.bulkify as bulk
    to_keep = {}
    # if not lexicon:
    #     lexicon = conf.keys()
    mapping = get_mapping(alias)
    index = make_indexname(alias, suffix)
    typ = configM.get_mode_type(alias)
    print('Save %s to %s' % (lexicon or 'all', index))

    es = configM.elastic(alias)
    if create_new:
        # Create the index
        ans = es.indices.create(index=index, body=mapping, request_timeout=30)
        print ans

    for lex in lexicon:
        engine, db_entry = db.get_engine(lex, echo=False)
        for entry in db.dbselect(lex, engine=engine, db_entry=db_entry, max_hits=-1):
            _id = entry['id']
            if _id:  # don't add things without id, they are errors
                if _id in to_keep:
                    last = to_keep[_id]['date']
                    if last < entry['date']:
                        to_keep[_id] = entry
                else:
                        to_keep[_id] = entry
    print len(to_keep), 'entries to keep'
    data = bulk.bulkify_sql(to_keep, bulk_info={'index': index, 'type': typ})
    try:
        ok, err = es_helpers.bulk(es, data, request_timeout=30)
    except:
        print data
    if err:
        msg = "Error during upload. %s documents successfully uploaded. \
               Message: %s.\n"
        raise Exception(msg % (ok, '\n'.join(err)))
    print 'recovery done'


def recover_add(index, suffix, lexicon):
    # TODO test this
    """ Recovers the data to ES, uses SQL as the trusted base version.
        Find the last version of every SQL entry and send this to ES.
        Adds the specified lexicons to an existing index
    """
    import karp_backend.server.translator.bulkify as bulk
    es = configM.elastic(index)
    print 'Save %s to %s' % (lexicon, index)
    to_keep = {}
    for lex in lexicon:
        engine, db_entry = db.get_engine(lex, echo=False)
        for entry in db.dbselect(lex, engine=engine, db_entry=db_entry,
                                 max_hits=-1):
            _id = entry['id']
            if _id:  # don't add things without id, they are errors
                if _id in to_keep:
                    last = to_keep[_id]['date']
                    if last < entry['date']:
                        to_keep[_id] = entry
                else:
                        to_keep[_id] = entry

    print len(to_keep), 'entries to keep'
    data = bulk.bulkify_sql(to_keep, bulk_info={'index': index})
    ok, err = es_helpers.bulk(es, data, request_timeout=30)
    if err:
        msg = "Error during upload. %s documents successfully uploaded. \
               Message: %s.\n"
        raise Exception(msg % (ok, '\n'.join(err)))
    print 'recovery done'


def printlatestversion(lexicon, debug=True, with_id=False):
    fp = sys.stdout
    to_keep = {}
    engine, db_entry = db.get_engine(lexicon, echo=False)
    count = 0
    for entry in db.dbselect(lexicon, engine=engine, db_entry=db_entry,
                             max_hits=-1):
        _id = entry['id']
        count += 1
        if _id:  # don't add things without id, they should not be here at all
            if _id in to_keep:
                last = to_keep[_id]['date']
                if last < entry['date']:
                    to_keep[_id] = entry
            else:
                    to_keep[_id] = entry

    if debug:
        print >> sys.stderr, 'count', count
    if with_id:
        gen_out = ({'_id': i, '_source': document.doc_to_es(val['doc'], lexicon, 'bulk')}
                   for i, val in six.viewitems(to_keep)
                   if val['status'] != 'removed')
    else:
        gen_out = (val['doc']
                   for val in six.viewvalues(to_keep)
                   if val['status'] != 'removed')
    json_iter.dump_array_fp(fp, gen_out)

def parse_config(name, info, default):
    """ Parse the info in lexiconconf.json and returns
        group, data, order, format
    """
    path = info.get('path', default.get('path', ''))
    fformat = info.get('format', default.get('format', 'json'))
    data = open('%s.%s' % (os.path.join(path, name), fformat), 'r').read()
    return info['mode'], data, info.get('order'), fformat


def make_parents(group):
    # a group is its own parent
    # (bliss should publish bliss170208, etc)
    parents = [group]
    for name, info in configM.searchconfig.items():
        if group in info.get('groups', []):
            parents.append(name)
    return parents


def publish_group(group, suffix):
    # TODO for some reason, this sometimes removes siblings
    # of the group from an mode. Eg. publish_group(saldo)
    # may lead to 'saldogroup' not containing 'external'.
    es = configM.elastic(group)
    print group, suffix
    if not configM.searchconfig.get(group)['is_index']:
        for subgroup in configM.searchconfig.get(group)['groups']:
            publish_group(subgroup, suffix)

    else:
        name = make_indexname(group, suffix)
        print "Publish %s as %s" % (name, group)
        add_actions = []
        rem_actions = []
        for parent in make_parents(group):
            add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}'
                               % (name, parent))
            rem_actions.append('{"remove": {"index":"%s_*", "alias":"%s"}}'
                               % (group, parent))

        print 'remove', rem_actions
        print 'add', add_actions
        try:
            print 'remove old aliases'
            es.indices.update_aliases('{"actions" : [%s]}' % ','.join(rem_actions), request_timeout=30)
        except Exception:
            print 'No previous aliased indices, could not do remove any'
            print rem_actions
        return es.indices.update_aliases('{"actions" : [%s]}' % ','.join(add_actions), request_timeout=30)


def create_empty_index(name, suffix, with_id=False):
    es = configM.elastic(name)
    data = get_mapping(name)
    newname = make_indexname(name, suffix)
    try:
        ans = es.indices.create(index=newname, body=data, request_timeout=30)
    except esExceptions.TransportError as e:
        print e
        raise Exception('Could not create index')
    print ans


def create_mode(alias, suffix, with_id=False):
    es = configM.elastic(alias)
    if configM.searchconfig[alias]['is_index']:
        to_create = [alias]
    else:
        to_create = configM.searchconfig.get(alias)['groups']

    typ = configM.searchconfig[alias]['type']
    for index in to_create:
        data = get_mapping(index)
        newname = make_indexname(index, suffix)
        try:
            ans = es.indices.create(index=newname, body=data, request_timeout=30)
        except esExceptions.TransportError as e:
            print e
            raise Exception('Could not create index')
        print ans
        try:
            lexicons = configM.get_lexiconlist(index)
            load(lexicons, newname, typ, es, with_id=with_id)
        except Exception as e:
            # delete the index if things did not go well
            ans = es.indices.delete(newname)
            print 'Any documentes uploaded to ES index %s are removed.' % newname
            print 'If data was uploaded to SQL you will have to \
                   remove it manually.'
            raise


def add_lexicon(to_add_name, to_add_file, alias, suffix):
    es = configM.elastic(alias)
    data = get_mapping(alias)
    indexname = make_indexname(alias, suffix)
    typ = configM.searchconfig[alias]['type']
    try:
        ans = es.indices.create(index=indexname, body=data, request_timeout=30)
        print ans
    except Exception:
        print 'Could not create index. Check if it needs manual removal'
        raise
    try:
        inpdata = open(to_add_file, 'r').read()
        sql = configM.get_mode_sql(alias)
        upload('json', to_add_name, '', inpdata, es, indexname, typ, sql=sql)
        # do this last to get the avoid version conflicts (in case some user is
        # updating the index during this process)
        reindex_alias(alias, suffix, create_index=False)

    except Exception:
        # delete the index if things did not go well
        ans = es.indices.delete(indexname)
        #print ans
        print 'Any documentes uploaded to ES index %s are removed.' % indexname
        print 'If data was uploaded to SQL you will have to \
               remove it manually.'
        raise


def internalize_lexicon(mode, to_add):
    """ Reads all entries from the lexicons specified in to_add
        and puts them in sql. They may then be edited.
        The ES index is not effected and this operation may hence
        be run at any time
    """
    ok = 0
    es = configM.elastic(mode)
    for lex in to_add:
        print 'Internalize', lex
        # Go through each lexicon separately
        query = {"query": {"term": {"lexiconName": lex}}}
        # scan and scroll
        ans = es_helpers.scan(es, query=query, scroll=u'3m', raise_on_error=True,
                           preserve_order=False, index=mode, request_timeout=30)
        sql_bulk = []
        for hit in ans:  # ans is an iterator of objects from in hits.hits
            _id = hit.get('_id')
            source = hit.get('_source')
            if not isinstance(source, dict):
                source = json.loads(source)
            sql_doc = document.doc_to_sql(source, lex, 'bulk')
            sql_bulk.append((_id, json.dumps(sql_doc), 'admin',
                             'entry automatically added or reloaded', lex,
                             'imported'))

        db_loaded, db_error = db.update_bulk(lex, sql_bulk)
        if db_error:
            raise Exception(db_error)
        ok += db_loaded

    print 'will load %s entries, starting with %s' % (len(sql_bulk), sql_bulk[0])
    if not ok:
        raise Exception("No data")
        print >> sys.stderr, "Warning. 0 documents uploaded\n"
    print "Ok. %s documents loaded to sql\n" % ok


def load(to_upload, index, typ, es, with_id=False):
    print 'Upload to %s' % index, ','.join(to_upload)
    try:
        for name, info in configM.lexiconconfig.items():
            if name in to_upload or not to_upload:
                default = configM.lexiconconfig.get('default', {})
                group, data, order, form = parse_config(name, info, default)
                sql = configM.searchconfig[group]['sql']
                print 'Upload %s. To sql? %s' % (name, sql)
                upload(form, name, order, data, es, index, typ, sql=sql,
                       with_id=with_id)
                print name, 'finished'
    except Exception:
        print '''Error during upload.
                 Check you\'re data bases for partially uploaded data.'''
        raise


def reindex(alias, source_suffix, target_suffix, create_index=True):
    source_index = make_indexname(alias, source_suffix)
    target_index = make_indexname(alias, target_suffix)
    reindex_help(alias, source_index, target_index, create_index=create_index)


def reindex_alias(alias, target_suffix, create_index=True):
    target_index = make_indexname(alias, target_suffix)
    reindex_help(alias, alias, target_index, create_index=create_index)


def reindex_help(alias, source_index, target_index, create_index=True):
    # TODO This function doesn't call doc_to_es
    print 'Reindex from %s to %s' % (source_index, target_index)
    es = configM.elastic(alias)
    if create_index:
        print 'create %s' % target_index
        data = get_mapping(alias)
        ans = es.indices.create(index=target_index, body=data, request_timeout=30)
        print 'Created index', ans

    source_docs = es_helpers.scan(es, size=10000, index=source_index, raise_on_error=True)

    def update_source_field(doc):
        doc['_source'] = document.doc_to_es(doc['_source'], alias, 'update')
        return doc

    update_docs = (update_source_field(doc) for doc in source_docs)
    ans = es_helpers.streaming_bulk(es, update_docs, index=target_index)
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    # ans = es_helpers.reindex(es, source_index, target_index)
    print ans


def publish_all(suffix):
    for alias, aliasconf in configM.searchconfig.items():
        # Only publish if it is a group, meta-aliases will point to the correct
        # subaliases anyway.
        if aliasconf['is_index']:
            publish_group(alias, suffix)


def make_structure():
    add_actions = []
    # TODO does not work, what is confelastic?
    for alias, aliasconf in configM.searchconfig.items():
        # Only publish if it is a group, meta-aliases will point to the correct
        # subaliases anyway.
        es = configM.elastic(alias)
        if not aliasconf.get("is_index"):
            # if it is a mode (not just an index), remove the old pointers
            add_actions.append('{"remove": {"index":"*", "alias":"%s"}}' % alias)
        for group in aliasconf.get('groups', []):
            add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}'
                               % (group, alias))

    return es.indices.update_aliases('{"actions" : [%s]}'
                                     % ','.join(add_actions), request_timeout=30)

def delete_all():
    # delete all indices
    for alias, aliasconf in configM.searchconfig.items():
        es = configM.elastic(alias)
        try:
            es.indices.delete('*')
        except:
            print 'could not delete es data form mode %s' % alias
        try:
            # delete all our lexicons in sql
            for name in configM.get_lexiconlist(alias):
                db.deletebulk(lexicon=name)
        except:
            print 'could not delete sql data form mode %s' % alias
    print 'Successfully deleted all data'


def delete_mode(mode):
    # delete all indices
    es = configM.elastic(mode)
    try:
        #print 'delete', '%s*' % mode
        es.indices.delete('%s*' % mode)
    except:
        print 'could not delete es data form mode %s' % mode
    try:
        # delete all our lexicons in sql
        for name in configM.get_lexiconlist(mode):
            db.deletebulk(lexicon=name)
    except:
        print 'could not delete sql data form mode %s' % mode
    print 'Successfully deleted all data'
