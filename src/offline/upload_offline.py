#!/usr/bin/python2
from elasticsearch import helpers
from elasticsearch import exceptions as esExceptions
import json
import sys

import config.modes as modes
from config.lexiconconf import conf
import src.dbhandler.dbhandler as db
import src.server.helper.configmanager as configM


def get_mapping(index):
    return 'config/mappings/mappingconf_%s.json' % index


def make_indexname(index, suffix):
    return index+'_'+suffix


def name_new_index():
    import datetime
    date = datetime.datetime.now().strftime('%Y%m%d')
    return 'karp' + date


def upload(informat, name, order, data, elastic, index, typ, sql=False,
           verbose=True, with_id=False):
    """ Uploads the data to elastic and the database
        sql      if True,  the data will be stored in the SQL data base as well
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
        print 'Error while reading data from %s' % name
        raise

    ok = 0
    if sql:
        # stream entries one by one to elastic, then update sql db
        # streaming_bulk will notify us at once when an entry fails
        sql_bulk = []
        for res in helpers.streaming_bulk(elastic, data):
            # res is a tuple, res[0]==True
            ansname = 'index' if with_id else 'create'
            _id = res[1].get(ansname).get('_id')
            source = data[ok].get('_source')
            if isinstance(source, dict):
                source = json.dumps(source)
            sql_bulk.append((_id, source, 'admin',
                             'entry automatically added or reloaded', name,
                             'imported'))
            ok += 1
        db_loaded, db_error = db.update_bulk(name, sql_bulk)
        if db_error:
            raise Exception(db_error)
        ok += db_loaded
    else:
        # upload all at once to elastic
        ok, err = helpers.bulk(elastic, data)
        if err:
            msg = "Error during upload. %s documents successfully uploaded. \
                   Message: %s.\n"
            raise Exception(msg % (ok, '\n'.join(err)))
    if not ok:
        raise Exception("No data")
        print >> sys.stderr, "Warning. 0 documents uploaded\n"
    if verbose:
        print "Ok. %s documents uploaded\n" % ok


def parse_upload(informat, lexname, lexorder, data, index, typ, with_id=False):
    """ Parse the query and the post and put it into the desired json format
    """
    from src.converter.lmftojson import get_lexicon
    import src.server.translator.bulkify as b

    bulk_info = {'index': index, 'type': typ}
    out_data = 0, [], []

    if informat == "xml":
        out_data = list(get_lexicon(data, lexname, lexorder=lexorder,
                                    make_bulk=False, bulk_info=bulk_info))

    elif informat == "json":
        out_data = b.bulkify(data, bulk_info, with_id=with_id)

    return out_data


# TODO outdated
# def reload_remove(elastic, index='', lexicon=[]):
#     """ Removes the data from SQL and loads a new version from file.
#     """
#     print 'Read new versions of %s to %s' % (lexicon or 'all', index)
#     # remove from sql
#     for name, info in conf.items():
#         if name in lexicon or not lexicon:
#             db.deletebulk(lexicon=name)
#     # load to new index and publish it
#     load_publish(elastic, index, lexicon)
#     print 'reloading done'


def recover(alias, suffix, lexicon, create_new=True):
    # TODO test this
    """ Recovers the data to ES, uses SQL as the trusted base version.
        Find the last version of every SQL entry and send this to ES.
    """
    import src.server.translator.bulkify as bulk
    to_keep = {}
    # if not lexicon:
    #     lexicon = conf.keys()
    mapping = get_mapping(alias)
    index = make_indexname(alias, suffix)
    typ = configM.get_mode_type(alias)
    print 'Save %s to %s' % (lexicon or 'all', index)

    es = configM.elastic(alias)
    if create_new:
        # Create the index
        ans = es.indices.create(index=index, body=open(mapping).read())
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
        ok, err = helpers.bulk(es, data)
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
    import src.server.translator.bulkify as bulk
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
    ok, err = helpers.bulk(es, data)
    if err:
        msg = "Error during upload. %s documents successfully uploaded. \
               Message: %s.\n"
        raise Exception(msg % (ok, '\n'.join(err)))
    print 'recovery done'


def printlatestversion(lexicon, debug=True, with_id=False):
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
        out = [{'_id': i, '_source': val['doc']} for i, val in to_keep.items()
               if val['status'] != 'removed']
        print json.dumps(out)
    else:
        print '\n'.join((json.dumps(val['doc']) for val in to_keep.values()
                         if val['status'] != 'removed'))


# TODO outdated. elastic, index, type and mapping are to be found in configs
# def reload_all(elastic, index='', lexiconmapping='', publish=True):
#     """ Reload data into a new index and then publish it
#         newindex  The name of the new index. Will be named after the current
#                   date, if not given
#         mapping   The file where the ES mapping is given
#         publish   Publish the index afterwards? Defaults to True
#     """
#     # if lexicon is not set, all lexica specified to our configuration should
#     # be used. Important when doing the recover() which will otherwise upload
#     # any other lexicon.
#     if not lexicon:
#         lexicon = conf.keys()
#     if not newindex:
#         newindex = name_new_index()
#     mapping = get_mapping(alias)
#
#     # Create the index
#     if not mapping:
#         mapping = _mapping
#     ans = es.indices.create(index=newindex, body=open(mapping).read())
#     print ans
#
#     # Read data from SQL to ES
#         # TODO must input lexicons, input suffix
#     recover(elastic, newindex, lexicon, create_new=False)
#
#     # Read external data from file to ES
#     for name, info in conf.items():
#         if name not in lexicon:
#             continue
#         group, data, order, form, sql, ext = parse_config(info, keep_external=False)
#         if not sql and not ext:  # upload all that are not stored in sql
#             print 'Upload %s. To sql? %s' % (name, sql)
#             upload(form, name, order, data, elastic, index, typ, sql=sql)
#             print name, 'finished'
#
#     # Publish index
#     if publish:
#         print "publish"
#         print publish_index(elastic, newindex)
#
#     return newindex


def parse_config(info, keep_external=True):
    """ Parse the info in lexiconconf.py and returns
        group, data, order, format
    """
    data = open(info[3], 'r').read()
    #      group    data  order    form
    return info[0], data, info[1], info[2]


# TODO outdated. elastic, index, type and mapping are to be found in configs
# def publish_index(es, newindex):
#     alias = setup.indexalias
#     aliasint = setup.index_internal
#     rem_actions = '''{"actions" : [{"remove" : {"index":"*", "alias":"%s"}}]}
#                   ''' % alias
#     add_actions = '''{"actions" : [{"add" : {"index": "%s", "alias": "%s"}}]}
#                   ''' % (newindex, alias)
#
#     try:
#         print 'remove old aliases'
#         es.indices.update_aliases(rem_actions)
#     except Exception:
#         print 'No previous aliased indices, could not do remove any'
#         print rem_actions
#     return es.indices.update_aliases(add_actions)


def make_parents(group):
    # a group is its own parent
    # (bliss should publish bliss170208, etc)
    parents = [group]
    for name, info in modes.modes.items():
        if group in info.get('groups', []):
            parents.append(name)
    return parents


def publish_group(group, suffix):
    # TODO for some reason, this sometimes removes siblings
    # of the group from an mode. Eg. publish_group(saldo)
    # may lead to 'saldogroup' not containing 'external'.
    es = configM.elastic(group)
    if not modes.modes.get(group)['is_index']:
        for subgroup in modes.modes.get(group)['groups']:
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
            es.indices.update_aliases('{"actions" : [%s]}' % ','.join(rem_actions))
        except Exception:
            print 'No previous aliased indices, could not do remove any'
            print rem_actions
        return es.indices.update_aliases('{"actions" : [%s]}' % ','.join(add_actions))


# TODO outdated. elastic, index, type and mapping are to be found in configs
# def load_publish(es, _index, to_upload, publish=False, mappnig=''):
#     data = open(_mapping, 'r').read()
#     try:
#         ans = es.indices.create(index=_index, body=data)
#     except esExceptions.TransportError as e:
#         print e
#         raise Exception('Index already exists')
#     print ans
#     try:
#         load(to_upload, _index, typ, es)
#     except Exception as e:
#         # delete the index if things did not go well
#         ans = es.indices.delete(_index)
#         print 'Any documentes uploaded to ES index %s are removed.' % _index
#         print 'If data was uploaded to SQL you will have to \
#                remove it manually.'
#         raise e
#     # print "publish"
#     # print publish_index(es, _index)

#    es.indices.update_aliases(add_actions)

def create_mode(alias, suffix, with_id=False):
    es = configM.elastic(alias)
    if modes.modes[alias]['is_index']:
        to_create = [alias]
    else:
        to_create = modes.modes.get(alias)['groups']

    typ = modes.modes[alias]['type']
    for index in to_create:
        data = open(get_mapping(index), 'r').read()
        newname = make_indexname(index, suffix)
        try:
            ans = es.indices.create(index=newname, body=data)
        except esExceptions.TransportError as e:
            print e
            raise Exception('Index already exists')
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
    data = open(get_mapping(alias), 'r').read()
    indexname = make_indexname(alias, suffix)
    typ = modes.modes[alias]['type']
    try:
        ans = es.indices.create(index=indexname, body=data)
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
        print ans
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
        ans = helpers.scan(es, query=query, scroll=u'3m', raise_on_error=True,
                           preserve_order=False, index=mode)
        sql_bulk = []
        for hit in ans:  # ans is an iterator of objects from in hits.hits
            _id = hit.get('_id')
            source = hit.get('_source')
            if isinstance(source, dict):
                source = json.dumps(source)
            sql_bulk.append((_id, source, 'admin',
                             'entry automatically added or reloaded', lex,
                             'imported'))

        db_loaded, db_error = db.update_bulk(lex, sql_bulk)
        if db_error:
            raise Exception(db_error)
        ok += db_loaded

    if not ok:
        raise Exception("No data")
        print >> sys.stderr, "Warning. 0 documents uploaded\n"
    print "Ok. %s documents loaded to sql\n" % ok


def load(to_upload, index, typ, es, with_id=False):
    print 'Upload to %s' % index, ','.join(to_upload)
    try:
        for name, info in conf.items():
            if name in to_upload or not to_upload:
                group, data, order, form = parse_config(info)
                sql = modes.modes[group]['sql']
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
    print 'Reindex from %s to %s' % (source_index, target_index)
    es = configM.elastic(alias)
    if create_index:
        print 'read %s' % get_mapping(alias), 'create %s' % target_index
        data = open(get_mapping(alias), 'r').read()
        ans = es.indices.create(index=target_index, body=data)
        print 'Created index', ans
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    ans = helpers.reindex(es, source_index, target_index)
    print ans


# TODO outdated. elastic, index, type and mapping are to be found in configs
# def reindex_except_lexicon(es, sourceindex, targetindex, _type, lexname):
#     print 'Copy data from %s to %s, excluding %s' % (sourceindex, targetindex, lexname)
#     reindex_some_lexicon(es, sourceindex, targetindex, _type, lexname, include=False)
#
# def reindex_partial_lexicon(es, sourceindex, targetindex, _type, lexname):
#     print 'Copy data from %s to %s, excluding %s' % (sourceindex, targetindex, lexname)
#     reindex_some_lexicon(es, sourceindex, targetindex, _type, lexname, include=True)
#
# def reindex_some_lexicon(es, sourceindex, targetindex, _type, lexname, include=True):
#     scan = helpers.scan(es, scroll=u'5m', index=sourceindex, doc_type=_type)
#     es_bulk, sql_bulk = [], []
#     num, discard = 0, 0
#     for hit in scan:
#         lexicon = hit['_source']['lexiconName']
#         if (lexname != lexicon and not include) or (lexname == lexicon and include):
#             es_bulk.append({'_index': targetindex, '_type': hit['_type'],
#                             '_id': hit['_id'], '_source': hit['_source']})
#             num+=1
#
#     data = open(_mapping, 'r').read()
#     ans = es.indices.create(index=targetindex, body=data)
#     print 'Created index', ans
#     # upload all at once to elastic
#     ok, err = helpers.bulk(es, es_bulk)
#     if err:
#         msg = "Error during upload. %s documents successfully uploaded. \
#                Message: %s.\n"
#         raise Exception(msg % (ok, '\n'.join(err)))
#     if not ok:
#         raise Exception("No data")
#         print >> sys.stderr, "Warning. 0 documents uploaded\n"
#     print "Ok. %s documents reindexed from %s to %s \n, %s discarded" % (num, sourceindex, targetindex, discard)


def publish_all(suffix):
    for alias, aliasconf in modes.modes.items():
        # Only publish if it is a group, meta-aliases will point to the correct
        # subaliases anyway.
        if aliasconf['is_index']:
            publish_group(alias, suffix)


def make_structure():
    add_actions = []
    for alias, aliasconf in modes.modes.items():
        # Only publish if it is a group, meta-aliases will point to the correct
        # subaliases anyway.
        es = confelastic(alias)
        if not aliasconf.get("is_index"):
            # if it is a mode (not just an index), remove the old pointers
            add_actions.append('{"remove": {"index":"*", "alias":"%s"}}' % alias)
        for group in aliasconf.get('groups', []):
            add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}'
                               % (group, alias))

    return es.indices.update_aliases('{"actions" : [%s]}'
                                     % ','.join(add_actions))

####################

usage = """Usage:
    'python upload_offline.py --help'     show this message

    'python upload_offline.py --recover indexName [lexicons]'\
     recover the current ES index from the SQL db

    'python upload_offline.py --publishnew index namemappingfile.json'\
     publish a new index with data from sql

    'python upload_offline.py [lexiconName,]'\
     upload lexicon to ES and SQL, as specified in lexiconconf.py
    """

if __name__ == "__main__":
    start_arg = 1

    if sys.argv[1] == '--help':
        # TODO outdated
        print usage

    elif sys.argv[1] == '--recover':
        print 'recover'
        index = sys.argv[2]
        suffix = sys.argv[3]
        recover(index, suffix, lexicon=sys.argv[4:], create_new=False)

    elif sys.argv[1] == '--recoveradd':
        print 'recover add', sys.argv[3:]
        index = sys.argv[2]
        suffix = sys.argv[3]
        recover_add(index, suffix, lexicon=sys.argv[4:])

    elif sys.argv[1] == '--reindexalias':
        print 'reindex'
        index = sys.argv[2]
        target_suffix = sys.argv[3]
        reindex_alias(index, target_suffix)

    elif sys.argv[1] == '--reindex':
        print 'reindex'
        index = sys.argv[2]
        source_suffix = sys.argv[3]
        target_suffix = sys.argv[4]
        reindex(index, source_suffix, target_suffix)

    # TODO outdated
    # elif sys.argv[1] == '--reload':
    #     print 'remove and reload'
    #     reload_remove(es, index=sys.argv[2], lexicon=sys.argv[3:])

    elif sys.argv[1] == '--printlatestversion':
        printlatestversion(sys.argv[2], debug=False)

    elif sys.argv[1] == '--exportlatestversion':
        printlatestversion(sys.argv[2], debug=False, with_id=True)

    # TODO outdated
    # elif sys.argv[1] == '--publishnew':
    #     print 'publish a new version'
    #     newindex = reload_all(es, newindex=sys.argv[2], publish=False)
    #     print 'All reloaded to', newindex

    elif sys.argv[1] == '--deleteindex':
        try:
            index = sys.argv[2]
            group = sys.argv[3]
            print 'Delete %s (belonging to %s)' % (index, group)
            es = configM.elastic(group)
            ans = es.indices.delete(index=index)
            print ans
        except esExceptions.TransportError as e:
            print 'Index %s was not present, can not be deleted' % index

    elif sys.argv[1] == '--getmapping':
        import offline.getmapping as gm
        alias = sys.argv[2]
        outfile = sys.argv[3]
        gm.getmapping(alias, outfile)

    # TODO outdated
    # elif sys.argv[1] == '--writemapping':
    #    import offline.getmapping as gm
    #    gm.getmapping(sys.argv[3:], outfile=sys.argv[2])

    # TODO outdated
    # elif sys.argv[1] == '--create_load':
    #     _index = sys.argv[2]
    #     start_arg = 3
    #     to_upload = sys.argv[start_arg:]
    #     load_publish(es, _index, to_upload, publish=False)
    #     print 'Upload successful'

    # TODO outdated
    # elif sys.argv[1] == '--create_load_publish':
    #     _index = sys.argv[2]
    #     start_arg = 3
    #     to_upload = sys.argv[start_arg:]
    #     load_publish(es, _index, to_upload)
    #     print 'Upload successful'

    elif sys.argv[1] == '--create_mode':
        # Creates every index (suffixed with 'suffix')
        # which are used in mode 'mode'
        # python upload_offline.py --create_mode karp 170119
        # will create seven indices (saldo_170119, bliss_170119 etc)
        mode = sys.argv[2]
        suffix = sys.argv[3]
        create_mode(mode, suffix)
        print 'Upload successful'

    elif sys.argv[1] == '--import_mode':
        # Creates every index (suffixed with 'suffix')
        # which are used in mode 'mode'
        # python upload_offline.py --import_mode karp 170119
        # will create seven indices (saldo_170119, bliss_170119 etc)
        # the input files should contain elastic IDs
        mode = sys.argv[2]
        suffix = sys.argv[3]
        create_mode(mode, suffix, with_id=True)
        print 'Upload successful'

    # TODO outdated
    # elif sys.argv[1] == '--load_to_existing':
    #     _index = sys.argv[2]
    #     start_arg = 3
    #     to_upload = sys.argv[start_arg:]
    #     load(to_upload, _index, es)
    #     print 'Upload successful'

    elif sys.argv[1] == '--add_lexicon':
        to_add_name = sys.argv[2]
        to_add_file = sys.argv[3]
        mode = sys.argv[4]
        suffix = sys.argv[5]
        add_lexicon(to_add_name, to_add_file, mode, suffix)
        print 'Upload successful'

    # TODO outdated
    elif sys.argv[1] == '--internalize_lexicon':
        # adds a lexicon to sql from es
        # can be done at any time, not noticable
        # to the end user
        mode = sys.argv[2]
        start_arg = 3
        to_upload = sys.argv[start_arg:]
        internalize_lexicon(mode, to_upload)
        print 'Upload successful'

    # TODO outdated
    # elif sys.argv[1] == '--reindex_remove':
    #     # TODO outdated
    #     sourceindex = sys.argv[2]
    #     targetindex = sys.argv[3]
    #     lexname = sys.argv[4]
    #     reindex_except_lexicon(es, sourceindex, targetindex, _type, lexname)

    # TODO outdated
    # elif sys.argv[1] == '--reindex_partial':
    #     sourceindex = sys.argv[2]
    #     targetindex = sys.argv[3]
    #     lexname = sys.argv[4]
    #     reindex_partial_lexicon(es, sourceindex, targetindex, _type, lexname)

    # elif sys.argv[1] == '--publish_index':
    #     # TODO outdated
    #     # publish an existing index and unpublish
    #     # the previous ones
    #     _index = sys.argv[2]
    #     publish_index(es, _index)
    #     print 'Upload successful'

    # elif sys.argv[1] == '--create_load_index':
    #     _index = sys.argv[2]
    #     mapping = sys.argv[3]
    #     start_arg = 4
    #     to_upload = sys.argv[start_arg:]
    #     load_publish(es, _index, to_upload, mapping=mapping)
    #     print 'Upload successful'

    elif sys.argv[1] == '--publish_group':
        # publish an existing group and unpublish
        # the previous ones
        group = sys.argv[2]
        suffix = sys.argv[3]
        publish_group(group, suffix)
        print 'Upload successful'

    elif sys.argv[1] == '--publish_all':
        # publish all modes
        suffix = sys.argv[2]
        publish_all(suffix)
        print 'All published'

    # TODO outdated
    # elif sys.argv[1] == '--make_structure':
    #     # initialize the alias structure (to be run once)
    #     make_structure()
    #     print 'Alias structure complete'

    else:
        print 'No valid flag recognised. Did you misspell the command?'
    # Commented since dangerous!
    # elif sys.argv[1] == '--delete_all':
    #     # delete all indices
    #     ans = es.indices.delete('*')
    #     # delete all our lexicons in sql
    #     for name in conf.keys():
    #         db.deletebulk(lexicon=name)
    #    print 'Successfully deleted all data'
