from __future__ import unicode_literals
def test_explain(client):
    response = client.get('/explain')

    assert response == 'searching.explain()'
    