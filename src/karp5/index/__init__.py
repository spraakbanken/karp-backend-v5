import logging

import elasticsearch
from elasticsearch import exceptions as es_errors

from karp5.config import mgr as conf_mgr
from karp5 import document


_logger = logging.getLogger('karp5')


def es_client(mode):
    return elasticsearch.Elasticsearch(
            conf_mgr.elasticnodes(mode=mode).
            )


def es_client_lexicon(lexicon):
    return elasticsearch.Elasticsearch(
            conf_mgr.elasticnodes(lexicon=lexicon)
            )


def create_index(mode, index):
    """ Create a new Elasticsearch index. """

    es = es_client(mode)
    mapping = conf_mgr.get_mapping(mode)
    try:
        ans = es.indices.create(
                index=index,
                body=mapping,
                request_timeout=30
            )
    except esExceptions.TransportError as e:
        _logger.exception(e)
        raise Exception('Could not create index')
    return ans


def search_scan_full(mode, index=None, query=None):
    return es_helpers.scan(
            es_client(mode),
            index=index if index else mode,
            query=query
            )


def copy_alias_to_index(
    source_mode,
    source_index,
    target_mode,
    target_index,
    create_index=True,
    query=None
):
    _logger.debug("Copying from '{source}' to '{target}' with query '{query}'".format(
        source=source_index if source_index else source_mode,
        target=target_index,
        query=query
        ))
    es_target = conf_mgr.elastic(target_mode)

    if create_index:
        create_index(target_mode, target_index)

    source_docs = search_scan_full(
        mode=source_mode,
        index=source_index,
        query=query
    )

    def update_doc(doc):
        """ Apply doc_to_es to doc. """
        doc['_source'] = document.doc_to_es(doc['_source'], target_mode, 'update')
        doc['_index'] = target_index
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
        _logger.debug('Done! Reindexed {} entries'.format(success))
        return True, success, None
    else:
        _logger.warning('Something went wrong!')
        _logger.warning('  - Successfully reindexed: {}'.format(success))
        _logger.warning('  - Failed to reindex: {}'.format(len(errors)))
        _logger.warning('This are the failing entries:')
        _logger.warning(errors)
        return False, success, errors

