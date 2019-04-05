import pytest

from karp5.cli import upload_offline as upload

@pytest.mark.parametrize('mode,facit',[
    ('panacea', ['panacea', 'karp'])
])
def test_make_parents(app, mode, facit):
    parents = upload.make_parents(mode)
    assert len(parents) == len(facit)
    for p, f in zip(parents, facit):
        assert p == f
    