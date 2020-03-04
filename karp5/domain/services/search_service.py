import itertools

import elasticsearch_dsl as es_dsl

from typing import Dict, Optional

from karp5.config import conf_mgr


def execute_query(es_search: es_dsl.Search, *, from_: int = 0, size: Optional[int] = None) -> Dict:
    if from_ is None:
        raise ValueError("'from_' must have a value.")

    response = {"hits": {"hits": [], "total": 0}}

    if size is None:
        tmp_search = es_search.extra(from_=0, size=0)
        tmp_response = tmp_search.execute()
        tot_hits = tmp_response.hits.total
        response["hits"]["total"] = tot_hits
        size = tot_hits - from_
        if tot_hits < from_:
            return response

    if size + from_ <= conf_mgr.app_config.SCAN_LIMIT:
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
        for hit in itertools.islice(es_search.scan(), from_, from_ + size):
            response["hits"]["hits"].append(hit.to_dict())

        return response

