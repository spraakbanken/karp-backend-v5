import json

import pytest


def get_json(client, path):
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


def test_autocomplete(client_w_panacea):
    q = "hatt"
    mode = "panacea"
    query = f"/autocomplete?q={ q }&mode={ mode }"

    result = get_json(client_w_panacea, query)

    print(f"result={ result }")
    assert result is None
