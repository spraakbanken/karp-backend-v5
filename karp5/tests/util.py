"""Testing utils."""
from base64 import b64encode
import json
import os

import elasticsearch_dsl as es_dsl


def mk_headers(username: str):
    """Create Authorization header for user.

    Arguments:
        username {str} -- the username to use

    Returns:
        {dict} -- The Authorization header to use
    """
    headers = {
        "Authorization": "Basic " + b64encode(username.encode("utf-8") + b":pwd").decode("utf-8")
    }
    return headers


def assert_es_search(first, second):
    print(f"first = {first}")
    print(f"second = {second}")
    es_first = es_dsl.Search.from_dict(first)
    es_second = es_dsl.Search.from_dict(second)
    assert es_first == es_second


def get_json(client, path: str):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


def post_json(client, path: str, doc: dict):
    response = client.post(path, data=json.dumps(doc), content_type="application/json")
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


tests_dir = os.path.abspath(os.path.dirname(__file__))
