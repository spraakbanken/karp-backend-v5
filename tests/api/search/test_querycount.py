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
def test_querycount(client_w_panacea, q, mode, n_hits):
    query = '/querycount?q={q}&mode={mode}'.format(q=q, mode=mode)
    result = get_json(client_w_panacea, query)

    assert 'distribution' in result
    if n_hits == 0:
        assert len(result['distribution']) == 0
    else:
        assert result['distribution'][0]['doc_count'] == n_hits
        assert len(result['distribution']) == 1
        assert len(result['distribution'][0]['lexiconName']['buckets']) == 1

    assert 'query' in result
    assert 'hits' in result['query']
    assert 'total' in result['query']['hits']
    assert result['query']['hits']['total'] == n_hits
