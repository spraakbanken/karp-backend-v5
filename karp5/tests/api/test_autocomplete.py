import json

import pytest


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


@pytest.mark.parametrize(
    "q,mode,n_hits",
    [("sit", "panacea", 2), ("set", "panacea", 26), ],
)
def test_autocomplete(client_w_panacea, q, mode, n_hits):
    query = f"/autocomplete?q={q}&mode={mode}"
    result = get_json(client_w_panacea, query)

    print(f"result = {result}")
    assert result is not None
    assert "hits" in result
    assert "hits" in result["hits"]
    hits = result["hits"]["hits"]
    assert len(hits) == n_hits
    assert result["hits"]["total"] == n_hits
