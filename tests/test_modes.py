from __future__ import unicode_literals


def test_modes(client):
    response = client.get("/modes")
    assert response.status_code == 200
