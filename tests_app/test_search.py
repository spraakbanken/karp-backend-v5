def test_explain(client):
    response = client.get('/explain')

    assert response == 'searching.explain()'
    