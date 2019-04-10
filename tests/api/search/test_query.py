import json


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


def test_query_reqexp_panacea(client_w_panacea):
    r1 = get_json(client_w_panacea, '/query?q=simple||sit&mode=panacea')

    assert 'hits' in r1
    assert 'total' in r1['hits']
    assert r1['hits']['total'] == 2

    r2 = get_json(client_w_panacea, '/query?q=simple||sit&mode=karp')

    assert 'hits' in r2
    assert 'total' in r2['hits']
    assert r2['hits']['total'] == 2
