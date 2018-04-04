#!/usr/bin/python2
from elasticsearch import helpers
from elasticsearch import exceptions as esExceptions
import json
import sys
import src.dbhandler.dbhandler as db
import src.server.helper.configmanager as configM
import os


def get_mapping(index):
    filepath =  'config/mappings/mappingconf_%s.json' % index
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
            ansname = 'index' # if with_id else 'create' -- changed from ES2
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
    import src.server.translator.bulkify as b

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
        ans = es.indices.create(index=index, body=mapping)
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
            es.indices.update_aliases('{"actions" : [%s]}' % ','.join(rem_actions))
        except Exception:
            print 'No previous aliased indices, could not do remove any'
            print rem_actions
        return es.indices.update_aliases('{"actions" : [%s]}' % ','.join(add_actions))


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
    data = get_mapping(alias)
    indexname = make_indexname(alias, suffix)
    typ = configM.searchconfig[alias]['type']
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
    print 'Reindex from %s to %s' % (source_index, target_index)
    es = configM.elastic(alias)
    if create_index:
        print 'create %s' % target_index
        data = get_mapping(alias)
        ans = es.indices.create(index=target_index, body=data)
        print 'Created index', ans
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    ans = helpers.reindex(es, source_index, target_index)
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
                                     % ','.join(add_actions))

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


####################

usage = """Usage:
    'python upload_offline.py --help'     show this message

    'python upload_offline.py --recover indexName [lexicons]'\
     recover the current ES index from the SQL db

    'python upload_offline.py --publishnew index namemappingfile.json'\
     publish a new index with data from sql

    'python upload_offline.py [lexiconName,]'\
     upload lexicon to ES and SQL, as specified in lexiconconf.json
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

    elif sys.argv[1] == '--printlatestversion':
        printlatestversion(sys.argv[2], debug=False)

    elif sys.argv[1] == '--exportlatestversion':
        printlatestversion(sys.argv[2], debug=False, with_id=True)

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

    elif sys.argv[1] == '--create_mode':
        # Creates every index (suffixed with 'suffix')
        # which are used in mode 'mode'
        # python upload_offline.py --create_mode karp 170119
        # will create seven indices (saldo_170119, bliss_170119 etc)
        mode = sys.argv[2]
        suffix = sys.argv[3]
        print 'Create %s_%s' % (mode, suffix)
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

    elif sys.argv[1] == '--add_lexicon':
        to_add_name = sys.argv[2]
        to_add_file = sys.argv[3]
        mode = sys.argv[4]
        suffix = sys.argv[5]
        add_lexicon(to_add_name, to_add_file, mode, suffix)
        print 'Upload successful'

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

    else:
        print 'No valid flag recognised. Did you misspell the command?'
