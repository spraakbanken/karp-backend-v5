"""Test the export endpoint."""
from hypothesis import given, settings, strategies as st

from karp5.tests.util import get_json


def test_export_panacea(client_w_panacea):
    query = "/export/panacea"
    results = get_json(client_w_panacea, query)

    assert "panacea" in results
    assert len(results["panacea"]) == 6609
    for obj in results["panacea"]:
        assert obj is not None
        assert "id" in obj
        assert obj["id"] is not None


@settings(deadline=None)
@given(st.integers(min_value=0, max_value=10000))
def test_export_panacea_w_size(client_w_panacea, size):
    query = f"/export/panacea?size={size}"
    results = get_json(client_w_panacea, query)

    assert "panacea" in results
    assert len(results["panacea"]) == min(size, 6609)
