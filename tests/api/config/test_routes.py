
import json


def get_json(client, path, status=(200, 300)):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert status[0] <= response.status_code < status[1]
    return json.loads(response.data.decode())


def test_route_modes(client):
    r = get_json(client, "/modes")

    assert "default" in r
    assert "panacea" in r
    assert "karp" in r
