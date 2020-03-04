import pytest

import elasticsearch_dsl as es_dsl

from karp5.domain.services import search_service
from karp5.config import conf_mgr


@pytest.mark.parametrize("from_,size", [
    (0, 25),
    (1000, 25),
    (10000, 25),
    (0, None),
    (15000, 15875)
])
def test_large_lex(app_w_large_lex, from_, size):
    mode = "large_lex"
    total_num_entries = 20000
    es_search = es_dsl.Search(using=conf_mgr.elastic(mode), index=mode)
    result = search_service.execute_query(es_search, from_=from_, size=size)
    if size is None:
        expected_len_hits = total_num_entries - from_
    else:
        expected_len_hits = size if (from_ + size < total_num_entries) else total_num_entries - from_

    assert len(result["hits"]["hits"]) == expected_len_hits
    assert result["hits"]["total"] == total_num_entries
    for hit in result["hits"]["hits"]:
        assert "_source" in hit
