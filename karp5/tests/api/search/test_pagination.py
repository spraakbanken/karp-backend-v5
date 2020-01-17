from hypothesis import assume, given, settings, strategies as st

from karp5.tests.util import get_json


@settings(deadline=None)
@given(start=st.sampled_from([0, 1, 40, 200, 264]), size=st.just(25))
# @given(start=st.integers(min_value=0), size=st.integers(min_value=0))
def test_pagination_panacea(client_w_panacea, start, size):
    command = "query"
    q = "extended||and|baseform|regexp|.*"
    mode = "panacea"
    query = f"/{command}?q={q}&mode={mode}&start={start}&size={size}"

    result = get_json(client_w_panacea, query)

    assert result is not None
    assert "hits" in result
    assert "hits" in result["hits"]
    if start > 6609:
        calculated_size = 0
    else:
        size_start = start + size
        if size_start < 6609:
            calculated_size = size
        else:
            calculated_size = min(size, 6609) - start

    # calculated_size = max(min(size + start, 6609) - start - 1, 0)
    assert len(result["hits"]["hits"]) == calculated_size


@settings(deadline=None)
@given(start=st.sampled_from([0, 1, 40, 200, 1000, 1500]), size=st.just(25))
# @given(start=st.integers(min_value=0), size=st.integers(min_value=0))
def test_pagination_large_lex(client_w_large_lex, start, size):
    command = "query"
    q = "extended||and|foo|regexp|.*"
    mode = "large_lex"
    query = f"/{command}?q={q}&mode={mode}&start={start}&size={size}"

    result = get_json(client_w_large_lex, query)

    assert result is not None
    assert "hits" in result
    assert "hits" in result["hits"]
    if start > 6609:
        calculated_size = 0
    else:
        size_start = start + size
        if size_start < 6609:
            calculated_size = size
        else:
            calculated_size = min(size, 6609) - start

    # calculated_size = max(min(size + start, 6609) - start - 1, 0)
    assert len(result["hits"]["hits"]) == calculated_size
