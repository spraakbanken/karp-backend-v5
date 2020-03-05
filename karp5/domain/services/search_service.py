import itertools
from typing import Dict, Optional

import attr
from elasticsearch import helpers as es_helpers
import elasticsearch_dsl as es_dsl

from karp5.config import conf_mgr


@attr.s(auto_attribs=True)
class SearchSettings:
    scan_limit: int = 10000


search_settings = SearchSettings()


def execute_query(es_search: es_dsl.Search, *, from_: int = 0, size: Optional[int] = None) -> Dict:
    if from_ is None:
        raise ValueError("'from_' must have a value.")

    response = {"hits": {"hits": [], "total": 0}}

    if size is None or (from_ + size > search_settings.scan_limit):
        # tmp_search = es_search.extra(from_=0, size=0)
        # tmp_response = tmp_search.execute()
        # tot_hits = tmp_response.hits.total
        tot_hits = es_search.count()
        response["hits"]["total"] = tot_hits
        if size is None:
            size = tot_hits - from_
        if tot_hits < from_:
            return response

    if size + from_ <= search_settings.scan_limit:
        extra_kwargs = {}
        if from_ is not None:
            extra_kwargs["from_"] = from_
        if size is not None:
            extra_kwargs["size"] = size
        if extra_kwargs:
            es_search = es_search.extra(**extra_kwargs)
        return es_search.execute().to_dict()
    else:
        es_search = es_search.params(preserve_order=True, scroll="5m")
        # Workaround
        scan_iter = es_helpers.scan(
            es_search._using,
            query=es_search.to_dict(),
            index=es_search._index,
            doc_type=es_search._get_doc_type(),
            **es_search._params
        )
        # scan_iter = es_search.scan()
        for hit in itertools.islice(scan_iter, from_, from_ + size):
            response["hits"]["hits"].append(hit)
            # response["hits"]["hits"].append(hit.to_dict())

        return response

