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
    es_search = es_dsl.Search(using=conf_mgr.elastic(mode), index=mode)
    result = search_service.execute_query(es_search, from_=from_, size=size)
    expected_len_hits = size - from_ if size else 20000

    assert len(result["hits"]["hits"]) == expected_len_hits
    assert result["hits"]["total"] == 20000
