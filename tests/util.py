import json
import os


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
