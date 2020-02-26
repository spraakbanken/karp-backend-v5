from karp5.tests.util import get_json


def test_logout(client):
    result = get_json(client, "/logout")

    assert result["logged_out"]

