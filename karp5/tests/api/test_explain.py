import pytest


from karp5.tests.util import get_json


@pytest.mark.parametrize(
    "q,mode,n_hits",
    [
        ("simple||sit", "panacea", 2),
        ("simple||sit", "karp", 2),
        ("extended||and|pos|exists", "panacea", 6609),
        ("extended||and|pos|equals|Vb", "panacea", 1677),
        ("extended||and|pos|missing", "panacea", 0),
        ("extended||and|baseform|startswith|ang", "panacea", 22),
        ("extended||and|baseform|startswith|ang|be", "panacea", 422),
        ("extended||and|pos|equals|Vb||and|baseform|startswith|ab", "panacea", 65),
        ("extended||and|baseform_en|regexp|s.*t", "panacea", 313),
        ("extended||and|pos|equals|Vb||not|baseform|startswith|ab", "panacea", 1612),
    ],
)
def test_explain(client_w_panacea, q, mode, n_hits):
    query = f"/explain?q={q}&mode={mode}"
    result = get_json(client_w_panacea, query)

    assert "elastic_json_query" in result
    assert "ans" in result
    assert "explain" in result
    assert "hits" in result["ans"]
    assert "total" in result["ans"]["hits"]
    assert result["ans"]["hits"]["total"] == n_hits
