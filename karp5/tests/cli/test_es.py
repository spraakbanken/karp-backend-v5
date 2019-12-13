from time import strftime

from elasticsearch import Elasticsearch
from elasticsearch import helpers as es_helpers
from elasticsearch import exceptions as esExceptions
import elasticsearch_dsl as es_dsl

import pytest

from karp5.config import mgr as conf_mgr
# from karp5.cli import upload_offline as upload


@pytest.mark.skip(reason="Only run separately.")
def test_scan():
    alias = "panacea"
    es = Elasticsearch(["http://localhost:9200"])
    target_index = "panacea_{}".format(strftime("%Y%m%d-%H%M%S"))
    data = conf_mgr.get_mapping(alias)
    try:
        ans = es.indices.create(index=target_index, body=data, request_timeout=30)
    except esExceptions.TransportError as e:
        raise Exception("Could not create index")

    print(ans)
    source_docs = es_helpers.scan(es, size=10000, index=alias, raise_on_error=True)

    def update_index(doc):
        doc["_index"] = target_index
        return doc

    updated_index = (update_index(doc) for doc in source_docs)
    success, failed, total = 0, 0, 0
    errors = []
    for ok, item in es_helpers.streaming_bulk(
        es, actions=updated_index, index=target_index
    ):
        if not ok:
            failed += 1
            errors.append(item)
        else:
            success += 1
            print("ok = {},item = {}".format(ok, item))
        total += 1
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    # ans = es_helpers.reindex(es, source_index, target_index)
    assert success == total


@pytest.mark.skip(reason="Doesn't work")
def test_dsl_scan():
    alias = "panacea"
    es = Elasticsearch(["http://localhost:9200"])
    s = es_dsl.Search(using=es, index=alias)
    target_index = "panacea_{}".format(strftime("%Y%m%d-%H%M%S"))
    data = conf_mgr.get_mapping(alias)
    try:
        ans = es.indices.create(index=target_index, body=data, request_timeout=30)
    except esExceptions.TransportError as e:
        raise Exception("Could not create index")

    print(ans)
    source_docs = s.scan()

    # for n, doc in enumerate(source_docs, 1):
    #     print(doc)
    #     assert '_source' in doc

    # assert n == 0
    def update_index(doc):
        doc["_index"] = target_index
        return doc

    updated_index = (update_index(doc) for doc in source_docs)
    success, failed, total = 0, 0, 0
    errors = []
    for ok, item in es_helpers.streaming_bulk(
        es, actions=source_docs, index=target_index
    ):
        if not ok:
            failed += 1
            errors.append(item)
        else:
            success += 1
            print("ok = {},item = {}".format(ok, item))
        total += 1
    # TODO when elasticsearch is updated to >=2.3: use es.reindex instead
    # ans = es_helpers.reindex(es, source_index, target_index)
    assert success != total
