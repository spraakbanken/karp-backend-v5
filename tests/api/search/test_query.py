import json

import pytest


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


@pytest.mark.parametrize('q,mode,n_hits',[
    ('simple||sit', 'panacea', 2),
    ('simple||sit', 'karp', 2),
    ('extended||and|pos|exists', 'panacea', 6609),
    ('extended||and|pos|missing', 'panacea', 0),
    ('extended||and|baseform|startswith|ang', 'panacea', 22),
    ('extended||and|pos|equals|Vb||and|baseform|startswith|ab', 'panacea', 65),
    ('extended||and|baseform_en|regexp|s.*t', 'panacea', 313),
    ('extended||and|pos|equals|Vb||not|baseform|startswith|ab', 'panacea', 1612),
])
def test_query(client_w_panacea, q, mode, n_hits):
    query = '/query?q={q}&mode={mode}'.format(q=q, mode=mode)
    result = get_json(client_w_panacea, query)

    assert 'hits' in result
    assert 'total' in result['hits']
    assert result['hits']['total'] == n_hits
