import pytest

from karp5.cli import upload_offline as upload


def test_create_empty_index(cli_w_es):
    r = cli_w_es.create_empty_index('panacea', 'test01')

    assert r.exit_code == 0


def test_copy_mode(client_w_panacea):
    r = client_w_panacea.get('/modes')

    assert r.status_code == 200
