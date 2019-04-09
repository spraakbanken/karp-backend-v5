import pytest

from karp5.cli import upload_offline as upload


def test_create_empty_index(app, es):
    if not es:
        pytest.skip('elasticsearch disabled')

    upload.create_empty_index('panacea', 'test')
    
