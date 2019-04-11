#!/usr/bin/python2
import json
import sys
import os
import logging

import six

from elasticsearch import helpers as es_helpers
from elasticsearch import exceptions as esExceptions

import karp5.dbhandler.dbhandler as db
from karp5.config import mgr as conf_mgr
from karp5.util import json_iter
from karp5 import document
from karp5.util.debug import print_err


_logger = logging.getLogger('karp5cli')

# ==============================================
# helpers
# ==============================================




def make_indexname(index, suffix):
    return index+'_'+suffix


def name_new_index():
    import datetime
    date = datetime.datetime.now().strftime('%Y%m%d')
    return 'karp' + date


def update_source_field(mode, doc):
    """ Apply doc_to_es to doc. """
    doc['_source'] = document.doc_to_es(doc['_source'], mode, 'update')
    return doc


def _create_index(mode, index):
    """ Create a new Elasticsearch index. """

    es = conf_mgr.elastic(mode)
    data = conf_mgr.get_mapping(mode)
    try:
        ans = es.indices.create(index=index, body=data, request_timeout=30)
    except esExceptions.TransportError as e:
        _logger.exception(e)
        raise Exception('Could not create index')
    print(ans)


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
        _logger.warning('No data. 0 documents uploaded.')
        raise Exception("No data")
    if verbose:
        print("Ok. %s documents uploaded\n" % ok)


def parse_upload(informat, lexname, lexorder, data, index, typ, with_id=False):
    """ Parse the query and the post and put it into the desired json format
    """
    import karp5.server.translator.bulkify as b

    bulk_info = {'index': index, 'type': typ}
    out_data = 0, [], []

    if informat == "json":
        out_data = b.bulkify(data, bulk_info, with_id=with_id)
    else:
        raise "Don't know how to parse %s" % informat

    return out_data


def get_entries_to_keep_from_sql(lexicons):
    to_keep = {}
    if isinstance(lexicons, six.text_type):
        lexicons = [lexicons]

    for lex in lexicons:
        engine, db_entry = db.get_engine(lex, echo=False)
        for entry in db.dbselect(lex, engine=engine, db_entry=db_entry, max_hits=-1):
            _id = entry['id']
            if _id:  # don't add things without id, they are errors
                if _id in to_keep:
                    last = to_keep[_id]['date']
                    if last < entry['date']:
                        _logger.debug('|get_entries_to_keep_from_sql| Update entry.')
                        to_keep[_id] = entry
                else:
                        to_keep[_id] = entry
            else:
                _logger.debug('|sql no id| Found entry without id:')
                _logger.debug('|sql no id| {}}'.format(entry))
    return to_keep


def recover(alias, suffix, lexicon, create_new=True):
    # TODO test this
    """ Recovers the data to ES, uses SQL as the trusted base version.
        Find the last version of every SQL entry and send this to ES.
    """
    import karp5.server.translator.bulkify as bulk
    # if not lexicon:
    #     lexicon = conf.keys()
    index = make_indexname(alias, suffix)
    typ = conf_mgr.get_mode_type(alias)
    print('Save %s to %s' % (lexicon or 'all', index))

    es = conf_mgr.elastic(alias)
    if create_new:
        # Create the index
        _create_index(alias, index)

    to_keep = get_entries_to_keep_from_sql(lexicon)
    print(len(to_keep), 'entries to keep')

    data = bulk.bulkify_sql(to_keep, bulk_info={'index': index, 'type': typ})
    try:
        ok, err = es_helpers.bulk(es, data, request_timeout=30)
    except:
        print(data)
    if err:
        msg = "Error during upload. %s documents successfully uploaded. \
               Message: %s.\n"
        raise Exception(msg % (ok, '\n'.join(err)))
    print('recovery done')


def recover_add(index, suffix, lexicon):
    # TODO test this
    """ Recovers the data to ES, uses SQL as the trusted base version.
        Find the last version of every SQL entry and send this to ES.
        Adds the specified lexicons to an existing index
    """
    import karp5.server.translator.bulkify as bulk
    es = conf_mgr.elastic(index)
    print('Save %s to %s' % (lexicon, index))

    to_keep = get_entries_to_keep_from_sql(lexicon)
    print(len(to_keep), 'entries to keep')

    data = bulk.bulkify_sql(to_keep, bulk_info={'index': index})
    ok, err = es_helpers.bulk(es, data, request_timeout=30)
    if err:
        msg = "Error during upload. %s documents successfully uploaded. \
               Message: %s.\n"
        raise Exception(msg % (ok, '\n'.join(err)))
    print('recovery done')


def printlatestversion(lexicon,
                       debug=True,
                       with_id=False,
                       file=None):
    if file:
        fp = file
    else:
        fp = sys.stdout

    to_keep = get_entries_to_keep_from_sql(lexicon)

    if debug:
        print_err('count', len(to_keep))

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


def publish_mode(mode, suffix):
    index = make_indexname(mode, suffix)
    add_actions = []
    rem_actions = []
    for alias in conf_mgr.get_modes_that_include_mode(mode):
        add_actions.append(
            '{"add" : {"index": "%s", "alias": "%s"}}' % (index, alias)
        )
        rem_actions.append(
            '{"remove": {"index":"%s_*", "alias":"%s"}}' % (mode, alias)
        )
    print('remove {}'.format(rem_actions))
    print('add {}'.format(add_actions))

    es = conf_mgr.elastic(mode)

    try:
        print('remove old aliases')
        es.indices.update_aliases(
            '{"actions" : [%s]}' % ','.join(rem_actions),
            request_timeout=30
        )
    except Exception:
        print('No previous aliased indices, could not do remove any')
        print(rem_actions)

    return es.indices.update_aliases(
        '{"actions" : [%s]}' % ','.join(add_actions),
        request_timeout=30
    )


def publish_group(group, suffix):
    # TODO for some reason, this sometimes removes siblings
    # of the group from an mode. Eg. publish_group(saldo)
    # may lead to 'saldogroup' not containing 'external'.
    es = conf_mgr.elastic(group)
    print(group, suffix)
    if not conf_mgr.modes.get(group)['is_index']:
        for subgroup in conf_mgr.modes.get(group)['groups']:
            publish_group(subgroup, suffix)

    else:
        name = make_indexname(group, suffix)
        print("Publish %s as %s" % (name, group))
        add_actions = []
        rem_actions = []
        for parent in conf_mgr.get_modes_that_include_mode(group):
            add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}'
                               % (name, parent))
            rem_actions.append('{"remove": {"index":"%s_*", "alias":"%s"}}'
                               % (group, parent))

        print('remove', rem_actions)
        print('add', add_actions)
        try:
            print('remove old aliases')
            es.indices.update_aliases('{"actions" : [%s]}' % ','.join(rem_actions), request_timeout=30)
        except Exception:
            print('No previous aliased indices, could not do remove any')
            print(rem_actions)
        return es.indices.update_aliases('{"actions" : [%s]}' % ','.join(add_actions), request_timeout=30)


def create_empty_index(mode, suffix):
    _create_index(mode, make_indexname(mode, suffix))





def create_mode(alias, suffix, with_id=False):
    es = conf_mgr.elastic(alias)
    if conf_mgr.modes[alias]['is_index']:
        to_create = [alias]
    else:
        to_create = conf_mgr.modes.get(alias)['groups']

    typ = conf_mgr.modes[alias]['type']
    for index in to_create:
        newname = make_indexname(index, suffix)
        _create_index(alias, newname)
        try:
            lexicons = conf_mgr.get_lexiconlist(index)
            load(lexicons, newname, typ, es, with_id=with_id)
        except Exception as e:
            # delete the index if things did not go well
            ans = es.indices.delete(newname)
            _logger.error('Any documentes uploaded to ES index %s are removed.' % newname)
            _logger.error('If data was uploaded to SQL you will have to remove it manually.')
            raise


def add_lexicon(to_add_name, to_add_file, alias, suffix):
    es = conf_mgr.elastic(alias)
    data = conf_mgr.get_mapping(alias)
    indexname = make_indexname(alias, suffix)
    typ = conf_mgr.modes[alias]['type']
    try:
        ans = es.indices.create(index=indexname, body=data, request_timeout=30)
        print(ans)
    except Exception:
        print('Could not create index. Check if it needs manual removal')
        raise
    try:
        inpdata = open(to_add_file, 'r').read()
        sql = conf_mgr.get_mode_sql(alias)
        upload('json', to_add_name, '', inpdata, es, indexname, typ, sql=sql)
        # do this last to get the avoid version conflicts (in case some user is
        # updating the index during this process)
        reindex_alias(alias, suffix, create_index=False)

    except Exception:
        # delete the index if things did not go well
        ans = es.indices.delete(indexname)
        #print(ans)
        _logger.error('Any documentes uploaded to ES index %s are removed.' % indexname)
        _logger.error('If data was uploaded to SQL you will have to remove it manually.')
        raise


def internalize_lexicon(mode, to_add):
    """ Reads all entries from the lexicons specified in to_add
        and puts them in sql. They may then be edited.
        The ES index is not effected and this operation may hence
        be run at any time
    """
    ok = 0
    es = conf_mgr.elastic(mode)
    for lex in to_add:
        print('Internalize', lex)
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

    print('will load %s entries, starting with %s' % (len(sql_bulk), sql_bulk[0]))
    if not ok:
        _logger.warning('No data. 0 documents uploaded.')
        raise Exception("No data")
    print("Ok. %s documents loaded to sql\n" % ok)


def load(to_upload, index, typ, es, with_id=False):
    print('Upload to %s' % index, ','.join(to_upload))
    try:
        for name, info in conf_mgr.lexicons.items():
            if name in to_upload or not to_upload:
                default = conf_mgr.lexicons.get('default', {})
                group, data, order, form = parse_config(name, info, default)
                sql = conf_mgr.modes[group]['sql']
                print('Upload %s. To sql? %s' % (name, sql))
                upload(form, name, order, data, es, index, typ, sql=sql,
                       with_id=with_id)
                print(name, 'finished')
    except Exception:
        _logger.error('''Error during upload.
                 Check you\'re data bases for partially uploaded data.''')
        raise


def copy_alias_to_new_index(
    source_mode,
    target_mode,
    target_suffix,
    create_index=True,
    query=None
):
    _logger.debug("Copying from")
    es_source = conf_mgr.elastic(source_mode)
    es_target = conf_mgr.elastic(target_mode)
    target_index = make_indexname(target_mode, target_suffix)
    if create_index:
        _create_index(target_mode, target_index)

    es_source_kwargs = {
        'index': source_mode
    }
    if query:
        es_source_kwargs['query'] = query
    source_docs = es_helpers.scan(es_source, **es_source_kwargs)

    update_docs = (update_source_field(target_mode, doc) for doc in source_docs)
    success, failed, total = 0, 0, 0
    errors = []
    for ok, item in es_helpers.streaming_bulk(es_target, update_docs, index=target_index):
        if not ok:
            failed += 1
            errors.append(item)
        else:
            success += 1
        total += 1
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    # ans = es_helpers.reindex(es, source_index, target_index)
    if success == total:
        print('Done! Reindexed {} entries'.format(total))
        return True, None
    else:
        print('Something went wrong!')
        print('  - Successfully reindexed: {}'.format(success))
        print('  - Failed to reindex: {}'.format(failed))
        print('This are the failing entries:')
        print(errors)
        return False, errors


def reindex(alias, source_suffix, target_suffix, create_index=True):
    source_index = make_indexname(alias, source_suffix)
    target_index = make_indexname(alias, target_suffix)
    reindex_help(alias, source_index, target_index, create_index=create_index)


def reindex_alias(alias, target_suffix, create_index=True):
    target_index = make_indexname(alias, target_suffix)
    reindex_help(alias, alias, target_index, create_index=create_index)


def reindex_help(alias, source_index, target_index, create_index=True):
    print('Reindex from %s to %s' % (source_index, target_index))
    es = conf_mgr.elastic(alias)
    if create_index:
        _create_index(alias, target_index)

    source_docs = es_helpers.scan(es, size=10000, index=source_index, raise_on_error=True)

    update_docs = (update_source_field(alias, doc) for doc in source_docs)
    success, failed, total = 0, 0, 0
    errors = []
    for ok, item in es_helpers.streaming_bulk(es, update_docs, index=target_index):
        if not ok:
            failed += 1
            errors.append(item)
        else:
            success += 1
        total += 1
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    # ans = es_helpers.reindex(es, source_index, target_index)
    if success == total:
        print('Done! Reindexed {} entries'.format(total))
    else:
        print('Something went wrong!')
        print('  - Successfully reindexed: {}'.format(success))
        print('  - Failed to reindex: {}'.format(failed))
        print('This are the failing entries:')
        print(errors)


def publish_all(suffix):
    for alias, aliasconf in conf_mgr.modes.items():
        # Only publish if it is a group, meta-aliases will point to the correct
        # subaliases anyway.
        if aliasconf['is_index']:
            publish_group(alias, suffix)


def make_structure():
    add_actions = []
    # TODO does not work, what is confelastic?
    for alias, aliasconf in conf_mgr.modes.items():
        # Only publish if it is a group, meta-aliases will point to the correct
        # subaliases anyway.
        es = conf_mgr.elastic(alias)
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
    for alias, aliasconf in conf_mgr.modes.items():
        es = conf_mgr.elastic(alias)
        try:
            es.indices.delete('*')
        except:
            print('could not delete es data form mode %s' % alias)
        try:
            # delete all our lexicons in sql
            for name in conf_mgr.get_lexiconlist(alias):
                db.deletebulk(lexicon=name)
        except:
            print('could not delete sql data form mode %s' % alias)
    print('Successfully deleted all data')


def delete_mode(mode):
    # delete all indices
    es = conf_mgr.elastic(mode)
    try:
        #print('delete', '%s*' % mode)
        es.indices.delete('%s*' % mode)
    except:
        print('could not delete es data form mode %s' % mode)
    try:
        # delete all our lexicons in sql
        for name in conf_mgr.get_lexiconlist(mode):
            db.deletebulk(lexicon=name)
    except:
        print('could not delete sql data form mode %s' % mode)
    print('Successfully deleted all data')
