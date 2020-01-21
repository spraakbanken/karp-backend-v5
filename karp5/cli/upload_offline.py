"""Handle lexicon and modes.
"""
import datetime
import json
import logging
import os
import sys
from typing import IO, Optional, List, Union

from elasticsearch import helpers as es_helpers
from elasticsearch import exceptions as esExceptions

from sb_json_tools import json_iter

# import elasticsearch_dsl as es_dsl

import karp5.dbhandler.dbhandler as db
from karp5.config import mgr as conf_mgr
from karp5 import document
from karp5.server.translator import bulkify


_logger = logging.getLogger("karp5")

# ==============================================
# helpers
# ==============================================


def make_indexname(index, suffix=None):
    if not suffix:
        suffix = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    return "{index}_{suffix}".format(index=index, suffix=suffix)


def update_source_field(mode, doc):
    """ Apply doc_to_es to doc. """
    doc["_source"] = document.doc_to_es(doc["_source"], mode, "update")
    return doc


def index_create(mode, index):
    """ Create a new Elasticsearch index. """

    es = conf_mgr.elastic(mode)
    data = conf_mgr.get_mapping(mode)
    try:
        _logger.debug("Creating index '%s' for mode '%s' with es=%s", index, mode, es)
        ans = es.indices.create(  # pylint: disable=unexpected-keyword-arg
            index=index, body=data, request_timeout=30
        )
    except esExceptions.TransportError as e:
        _logger.exception(e)
        raise Exception("Could not create index")
    return ans


def index_exists(mode: str, index: Union[str, List[str]]) -> bool:
    """Check if index exists for mode.

    Arguments:
        mode {str} -- the mode to query from
        index {str} -- the index to to query for

    Returns:
        bool -- wheter the index exists or not
    """
    es = conf_mgr.elastic(mode)
    ans = es.indices.exists(index=index)
    print(f"index_exists: and = {ans}")
    return ans


def upload(
    informat, name, order, data, elastic, index, typ, sql=False, verbose=True, with_id=False,
):
    """Uploads the data to elastic and the database
        sql      if True,  the data will be stored in the SQL database as well
                 as ElasticSearch
                 if False, the data will only be stored in ElasticSearch
        informat can either be xml  - lmf
                               json - a single json object or a list of objects
                               bulk - a list of json objects annotated with
                                      index and type information, as accepted
                                      by ElasticSearch

    Arguments:
        informat {[type]} -- [description]
        name {[type]} -- [description]
        order {[type]} -- [description]
        data {[type]} -- [description]
        elastic {[type]} -- [description]
        index {[type]} -- [description]
        typ {[type]} -- [description]

    Keyword Arguments:
        sql {bool} -- [description] (default: {False})
        verbose {bool} -- [description] (default: {True})
        with_id {bool} -- [description] (default: {False})

    Raises:
        Exception: [description]
        Exception: [description]
        Exception: [description]
        Exception: [description]
        Exception: [description]
        Exception: [description]
        Exception: [description]

    Returns:
        [type] -- [description]
    """
    try:
        # The actual parsing
        data = parse_upload(informat, name, order, data, index, typ, with_id=with_id)
    except Exception:
        print("Error while reading data from %s" % name)
        raise

    ok = 0
    if sql:
        # stream entries one by one to elastic, then update sql db
        # streaming_bulk will notify us at once when an entry fails
        sql_bulk = []
        for res in es_helpers.streaming_bulk(elastic, data, request_timeout=60):
            # res is a tuple, res[0]==True
            ansname = "index"  # if with_id else 'create' -- changed from ES2
            _id = res[1].get(ansname).get("_id")
            data_doc = data[ok].get("_source")
            if not isinstance(data_doc, dict):
                data_doc = json.loads(data_doc)
            sql_doc = document.doc_to_sql(data_doc, data_doc["lexiconName"], "bulk")
            sql_bulk.append(
                (
                    _id,
                    json.dumps(sql_doc),
                    "admin",
                    "entry automatically added or reloaded",
                    name,
                    "imported",
                )
            )
            ok += 1
        db_loaded, db_error = db.update_bulk(name, sql_bulk)
        if db_error:
            _logger.error("Got DB error: %s", db_error)
            raise Exception(db_error)
        ok += db_loaded
    else:
        # upload all at once to elastic
        ok, err = es_helpers.bulk(elastic, data, request_timeout=60)
        if err:
            msg = "Error during upload. %s documents successfully uploaded. \
                   Message: %s.\n"
            raise Exception(msg % (ok, "\n".join(err)))
    if not ok:
        _logger.warning("No data. 0 documents uploaded.")
        raise Exception("No data")
    if verbose:
        print("Ok. %s documents uploaded\n" % ok)


def parse_upload(informat, lexname, lexOrder, data, index, typ, with_id=False):
    """Parse the query and the post and put it into the desired json format

    Arguments:
        informat {[type]} -- [description]
        lexname {[type]} -- [description]
        lexOrder {[type]} -- [description]
        data {[type]} -- [description]
        index {[type]} -- [description]
        typ {[type]} -- [description]

    Keyword Arguments:
        with_id {bool} -- [description] (default: {False})

    Returns:
        [type] -- [description]
    """

    bulk_info = {"index": index, "type": typ}
    out_data = 0, [], []

    if informat == "json":
        out_data = bulkify.bulkify(data, bulk_info, with_id=with_id)
    else:
        raise "Don't know how to parse %s" % informat

    return out_data


# def get_entries_to_keep_from_sql(lexicons):
#     to_keep = {}
#     if isinstance(lexicons, six.text_type):
#         lexicons = [lexicons]

#     for lex in lexicons:
#         engine, db_entry = db.get_engine(lex, echo=False)
#         for entry in db.dbselect(lex, engine=engine, db_entry=db_entry, max_hits=-1):
#             _id = entry["id"]
#             if _id:  # don't add things without id, they are errors
#                 if _id in to_keep:
#                     last = to_keep[_id]["date"]
#                     if last < entry["date"]:
#                         _logger.debug("|get_entries_to_keep_from_sql| Update entry.")
#                         to_keep[_id] = entry
#                 else:
#                     to_keep[_id] = entry
#             else:
#                 _logger.warning("|sql no id| Found entry without id:")
#                 _logger.warning("|sql no id| %s", entry)
#     # _logger.debug("to_keep = %s", to_keep)
#     return to_keep


def recover(alias, suffix, lexicon, create_new=True) -> bool:
    """ Recovers the data to ES, uses SQL as the trusted base version.
        Find the last version of every SQL entry and send this to ES.
    """

    # if not lexicon:
    #     lexicon = conf.keys()
    index = make_indexname(alias, suffix)
    index_type = conf_mgr.get_mode_type(alias)
    print("Save %s to %s" % (lexicon or "all", index))

    es = conf_mgr.elastic(alias)
    if create_new:
        # Create the index
        index_create(alias, index)

    # to_keep = get_entries_to_keep_from_sql(lexicon)
    # print(len(to_keep), "entries to keep")
    entries = db.get_entries_to_keep_gen(lexicon)

    data = bulkify.bulkify_from_sql(entries, index, index_type)
    ok, err = es_helpers.bulk(es, data, request_timeout=30)
    if err:
        msg = "Error during upload. %s documents successfully uploaded. \
               Message: %s.\n"
        raise Exception(msg % (ok, "\n".join(err)))
    print("recovery done")
    return True


# def recover_add(index, suffix, lexicon):
#     # xTODO test this
#     """ Recovers the data to ES, uses SQL as the trusted base version.
#         Find the last version of every SQL entry and send this to ES.
#         Adds the specified lexicons to an existing index
#     """

#     es = conf_mgr.elastic(index)
#     print("Save %s to %s" % (lexicon, index))

#     to_keep = get_entries_to_keep_from_sql(lexicon)
#     print(len(to_keep), "entries to keep")

#     data = bulkify.bulkify_sql(to_keep, bulk_info={"index": index})
#     ok, err = es_helpers.bulk(es, data, request_timeout=30)
#     if err:
#         msg = "Error during upload. %s documents successfully uploaded. \
#                Message: %s.\n"
#         raise Exception(msg % (ok, "\n".join(err)))
#     print("recovery done")


def printlatestversion(lexicon: str, with_id: bool = False, fp: Optional[IO] = None):
    """Dump the latest entries for a lexicon (or mode?).

       If with_id=True, then the results can be imported from cli.
    Arguments:
        lexicon -- the lexicon to print

    Keyword Arguments:
        debug -- whether to print debug information (default: {True})
        with_id -- if True, prints the entries as in ElasticSearch (default: {False})
        fp -- file handle to write to, if None write to stdout (default: {None})
    """
    if fp is None:
        fp = sys.stdout

    # to_keep = get_entries_to_keep_from_sql(lexicon)
    entries = db.get_entries_to_keep_gen(lexicon)

    if with_id:
        entries = (
            {"_id": entry["id"], "_source": document.doc_to_es(entry["doc"], lexicon, "bulk")}
            for entry in entries
        )
    else:
        entries = (entry["doc"] for entry in entries)

    json_iter.dump(entries, fp)


def publish_mode(mode, suffix):
    index = make_indexname(mode, suffix)
    add_actions = []
    rem_actions = []
    for alias in conf_mgr.get_modes_that_include_mode(mode):
        add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}' % (index, alias))
        rem_actions.append('{"remove": {"index":"%s_*", "alias":"%s"}}' % (mode, alias))
    print("remove {}".format(rem_actions))
    print("add {}".format(add_actions))

    es = conf_mgr.elastic(mode)

    try:
        print("remove old aliases")
        es.indices.update_aliases(  # pylint: disable=unexpected-keyword-arg
            '{"actions" : [%s]}' % ",".join(rem_actions), request_timeout=30
        )  # pylint: disable=unexpected-keyword-arg
    except esExceptions.ElasticsearchException:
        print("No previous aliased indices, could not do remove any")
        print(rem_actions)

    return es.indices.update_aliases(  # pylint: disable=unexpected-keyword-arg
        '{"actions" : [%s]}' % ",".join(add_actions), request_timeout=30
    )


# TODO Is this used?
# def publish_group(group, suffix):
#     # xTODO for some reason, this sometimes removes siblings
#     # of the group from an mode. Eg. publish_group(saldo)
#     # may lead to 'saldogroup' not containing 'external'.
#     es = conf_mgr.elastic(group)
#     print(group, suffix)
#     if not conf_mgr.modes.get(group)["is_index"]:
#         for subgroup in conf_mgr.modes.get(group)["groups"]:
#             publish_group(subgroup, suffix)

#     else:
#         name = make_indexname(group, suffix)
#         print("Publish %s as %s" % (name, group))
#         add_actions = []
#         rem_actions = []
#         for parent in conf_mgr.get_modes_that_include_mode(group):
#             add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}' % (name, parent))
#             rem_actions.append('{"remove": {"index":"%s_*", "alias":"%s"}}' % (group, parent))

#         print("remove", rem_actions)
#         print("add", add_actions)
#         try:
#             print("remove old aliases")
#             es.indices.update_aliases(
#                 '{"actions" : [%s]}' % ",".join(rem_actions), request_timeout=30
#             )
#         except Exception:
#             print("No previous aliased indices, could not do remove any")
#             print(rem_actions)
#         return es.indices.update_aliases(
#             '{"actions" : [%s]}' % ",".join(add_actions), request_timeout=30
#         )


def create_empty_index(mode, suffix):
    return index_create(mode, make_indexname(mode, suffix))


def create_mode(alias, suffix, with_id=False, data_dir=None):
    """[summary]

    Arguments:
        alias {[type]} -- [description]
        suffix {[type]} -- [description]

    Keyword Arguments:
        with_id {bool} -- [description] (default: {False})
        data_dir -- Path to load lexicons from. (default: {None})
    """
    es = conf_mgr.elastic(alias)
    if conf_mgr.modes[alias]["is_index"]:
        to_create = [alias]
    else:
        to_create = conf_mgr.modes.get(alias)["groups"]

    typ = conf_mgr.modes[alias]["type"]
    for index in to_create:
        newname = make_indexname(index, suffix)
        index_create(alias, newname)
        try:
            lexicons = conf_mgr.get_lexiconlist(index)
            load(lexicons, newname, typ, es, with_id=with_id, data_dir=data_dir)
        except Exception as e:
            # delete the index if things did not go well
            ans = es.indices.delete(newname)
            _logger.error(
                "Any documentes uploaded to ES index %s are removed. ans = '%s'", newname, ans,
            )
            _logger.error("If data was uploaded to SQL you will have to remove it manually.")
            _logger.exception(e)
            raise


def add_lexicon(lexicon, suffix, filename=None, with_id=False):
    mode = conf_mgr.get_lexicon_mode(lexicon)
    es = conf_mgr.elastic(mode)
    indexname = make_indexname(mode, suffix)
    _type = conf_mgr.modes[mode]["type"]
    _logger.debug(
        "add_lexicon(lexicon=%s suffix=%s filename=%s with_id=%s)",
        lexicon,
        suffix,
        filename,
        with_id,
    )
    _logger.debug(" -> mode=%s indexname=%s es=%s", mode, indexname, es)
    if not es.indices.exists(indexname):
        try:
            ans = index_create(mode, indexname)
        except Exception:
            print("Could not create index. Check if it needs manual removal")
            raise
    try:
        if filename is None:
            filename = conf_mgr.default_filename(lexicon)
        with open(filename, "r") as fp:
            data = fp.read()
        sql = conf_mgr.get_mode_sql(mode)
        upload("json", lexicon, "", data, es, indexname, _type, sql=sql, with_id=with_id)
        # do this last to get the avoid version conflicts (in case some user is
        # updating the index during this process)
        # reindex_alias(mode, suffix, create_index=False)

    except Exception as e:
        # delete the index if things did not go well
        ans = es.indices.delete(indexname)
        # print(ans)
        _logger.error("Any documentes uploaded to ES index %s are removed. ans=%s", indexname, ans)
        _logger.error("If data was uploaded to SQL you will have to remove it manually.")
        _logger.exception(e)
        raise
    return indexname


def internalize_lexicon(mode, to_add):
    """ Reads all entries from the lexicons specified in to_add
        and puts them in sql. They may then be edited.
        The ES index is not effected and this operation may hence
        be run at any time
    """
    ok = 0
    es = conf_mgr.elastic(mode)
    for lex in to_add:
        print("Internalize", lex)
        # Go through each lexicon separately
        query = {"query": {"term": {"lexiconName": lex}}}
        # scan and scroll
        ans = es_helpers.scan(
            es,
            query=query,
            scroll="3m",
            raise_on_error=True,
            preserve_order=False,
            index=mode,
            request_timeout=30,
        )
        sql_bulk = []
        for hit in ans:  # ans is an iterator of objects from in hits.hits
            _id = hit.get("_id")
            source = hit.get("_source")
            if not isinstance(source, dict):
                source = json.loads(source)
            sql_doc = document.doc_to_sql(source, lex, "bulk")
            sql_bulk.append(
                (
                    _id,
                    json.dumps(sql_doc),
                    "admin",
                    "entry automatically added or reloaded",
                    lex,
                    "imported",
                )
            )

        db_loaded, db_error = db.update_bulk(lex, sql_bulk)
        if db_error:
            raise Exception(db_error)
        ok += db_loaded

    print("will load %s entries, starting with %s" % (len(sql_bulk), sql_bulk[0]))
    if not ok:
        _logger.warning("No data. 0 documents uploaded.")
        raise Exception("No data")
    print("Ok. %s documents loaded to sql\n" % ok)


def load(to_upload, index, typ, es, with_id: bool = False, data_dir: str = None):
    """[summary]

    Arguments:
        to_upload {[type]} -- [description]
        index {[type]} -- [description]
        typ {[type]} -- [description]
        es {[type]} -- [description]

    Keyword Arguments:
        with_id {bool} -- [description] (default: {False})
        data_dir {[type]} -- [description] (default: {None})
    """
    print("Upload to %s" % index, ",".join(to_upload))
    try:
        for lexicon, info in conf_mgr.lexicons.items():
            if lexicon in to_upload or not to_upload:
                default = conf_mgr.lexicons.get("default", {})
                file_format = info.get("format", default.get("format", "json"))
                if data_dir is not None:
                    filename = os.path.join(data_dir)
                filename = conf_mgr.default_filename(lexicon)
                with open(filename, "r") as fp:
                    _logger.info("reading file '%s'", filename)
                    data = fp.read()
                sql = conf_mgr.modes[info["mode"]]["sql"]
                _logger.info("Upload %s. To sql? %s", lexicon, sql)
                upload(
                    file_format,
                    lexicon,
                    info["order"],
                    data,
                    es,
                    index,
                    typ,
                    sql=sql,
                    with_id=with_id,
                )
                _logger.info("Upload of %s finished.", lexicon)
    except Exception:
        _logger.error(
            """Error during upload.
                 Check you're data bases for partially uploaded data."""
        )
        raise


def apply_filter(it, filter_func, field=None):
    """
    Apply the given func to every object in it.

    :param it: The iterable.
    :param filter_func: The func to apply. Must return an iterable.
    :param field: str
    """
    if not field:
        field = "_source"
    filtered = []
    for i in it:
        for x in filter_func(i[field], i["_id"]):
            filtered.append({field: x})
    return filtered


def copy_alias_to_new_index(
    source_mode, target_mode, target_suffix, filter_func=None, create_index=True, query=None,
):
    es_source = conf_mgr.elastic(source_mode)
    es_target = conf_mgr.elastic(target_mode)
    target_index = make_indexname(target_mode, target_suffix)
    _logger.debug("Copying from '%s' to '%s'", source_mode, target_index)
    if create_index:
        index_create(target_mode, target_index)

    source_docs = es_helpers.scan(es_source, index=source_mode, query=query)

    if filter_func:
        source_docs = apply_filter(source_docs, filter_func)

    target_type = conf_mgr.get_mode_type(target_mode)

    def update_doc(doc):
        """ Apply doc_to_es to doc. """
        doc["_source"] = document.doc_to_es(doc["_source"], target_mode, "update")
        doc["_index"] = target_index
        doc["_type"] = target_type
        return doc

    update_docs = (update_doc(doc) for doc in source_docs)
    success = 0
    errors = []
    for ok, item in es_helpers.streaming_bulk(es_target, update_docs, index=target_index):
        if not ok:
            errors.append(item)
        else:
            success += 1
    if len(errors) == 0:
        print("Done! Reindexed {} entries".format(success))
        return True, None
    else:
        print("Something went wrong!")
        print("  - Successfully reindexed: {}".format(success))
        print("  - Failed to reindex: {}".format(len(errors)))
        print("This are the failing entries:")
        print(errors)
        return False, errors


def reindex(alias, source_suffix, target_suffix, create_index=True):
    source_index = make_indexname(alias, source_suffix)
    target_index = make_indexname(alias, target_suffix)
    return reindex_help(alias, source_index, target_index, create_index=create_index)


def reindex_alias(alias, target_suffix, create_index=True):
    target_index = make_indexname(alias, target_suffix)
    return reindex_help(alias, alias, target_index, create_index=create_index)


def reindex_help(alias, source_index, target_index, create_index=True):
    print("Reindex from %s to %s" % (source_index, target_index))
    es = conf_mgr.elastic(alias)
    if create_index:
        index_create(alias, target_index)

    source_docs = es_helpers.scan(es, size=10000, index=source_index, raise_on_error=True)

    def update_doc(doc):
        """ Apply doc_to_es to doc. """
        doc["_source"] = document.doc_to_es(doc["_source"], alias, "update")
        doc["_index"] = target_index
        return doc

    update_docs = (update_doc(doc) for doc in source_docs)
    success, failed, total = 0, 0, 0
    errors = []
    for ok, item in es_helpers.streaming_bulk(es, update_docs, index=target_index):
        if not ok:
            failed += 1
            errors.append(item)
        else:
            success += 1
            print("ok = {},item = {}".format(ok, item))
        total += 1
    if success == total:
        _logger.info("Done! Reindexed %s entries", total)
        return True
    else:
        _logger.warning("Something went wrong!")
        _logger.warning("  - Successfully reindexed: %s", success)
        _logger.warning("  - Failed to reindex: %s", failed)
        _logger.warning("This are the failing entries:")
        _logger.warning(errors)
        return False


# TODO Is this used?
# def publish_all(suffix):
#     for alias, aliasconf in conf_mgr.modes.items():
#         # Only publish if it is a group, meta-aliases will point to the correct
#         # subaliases anyway.
#         if aliasconf["is_index"]:
#             publish_group(alias, suffix)


# TODO Is this used?
# def make_structure():
#     add_actions = []
#     # xTODO does not work, what is confelastic?
#     for alias, aliasconf in conf_mgr.modes.items():
#         # Only publish if it is a group, meta-aliases will point to the correct
#         # subaliases anyway.
#         es = conf_mgr.elastic(alias)
#         if not aliasconf.get("is_index"):
#             # if it is a mode (not just an index), remove the old pointers
#             add_actions.append('{"remove": {"index":"*", "alias":"%s"}}' % alias)
#         for group in aliasconf.get("groups", []):
#             add_actions.append('{"add" : {"index": "%s", "alias": "%s"}}' % (group, alias))

#     return es.indices.update_aliases(
#         '{"actions" : [%s]}' % ",".join(add_actions), request_timeout=30
#     )


def delete_all():
    # delete all indices
    for alias, _ in conf_mgr.modes.items():
        es = conf_mgr.elastic(alias)
        try:
            es.indices.delete("*")
        except esExceptions.ElasticsearchException:
            print("could not delete es data form mode %s" % alias)
        try:
            # delete all our lexicons in sql
            for name in conf_mgr.get_lexiconlist(alias):
                db.deletebulk(lexicon=name)
        except Exception:
            print("could not delete sql data form mode %s" % alias)
    print("Successfully deleted all data")


def delete_mode(mode):
    # delete all indices
    es = conf_mgr.elastic(mode)
    try:
        # print('delete', '%s*' % mode)
        es.indices.delete("%s*" % mode)
    except esExceptions.ElasticsearchException:
        print("could not delete es data form mode %s" % mode)
    try:
        # delete all our lexicons in sql
        for name in conf_mgr.get_lexiconlist(mode):
            db.deletebulk(lexicon=name)
    except Exception:
        print("could not delete sql data form mode %s" % mode)
    print("Successfully deleted all data")
