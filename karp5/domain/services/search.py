import elasticsearch_dsl as es_dsl

from typing import Dict, Optional

from karp5.config import conf_mgr


def execute_query(
    es_search: es_dsl.Search, *, from_: Optional[int] = None, size: Optional[int] = None
) -> Dict:
    if size is None:
        tmp_search = es_search.extra(from_=0, size=0)
        tmp_response = tmp_search.execute()
        size = tmp_response.hits.total
        es_search = es_search.params(preserve_order=True, scroll="5m")
        response = {"hits": {"hits": [], "total": tmp_response.hits.total}}
        for hit in es_search.scan():
            response["hits"]["hits"].append(hit.to_dict())

        return response
    extra_kwargs = {}
    if from_ is not None:
        extra_kwargs["from_"] = from_
    if size is not None:
        extra_kwargs["size"] = size
    if extra_kwargs:
        es_search = es_search.extra(**extra_kwargs)
    return es_search.execute().to_dict()
