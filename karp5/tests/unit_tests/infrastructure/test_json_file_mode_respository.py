from pathlib import Path

import pytest

from karp5.infrastructure.json_file_mode_repository import JsonFileModeRepository


@pytest.fixture(name="mode_repo", scope="session")
def fixture_mode_repo():
    return JsonFileModeRepository(config_dir=Path("karp5/tests/data/config"))


def test_json_file_mode_repository(mode_repo):

    assert mode_repo.mode_ids() == ["panacea", "panacea_links", "karp", "foo", "large_lex"]

    for mode_id in mode_repo.mode_ids():
        mode = mode_repo.mode_by_id(mode_id)

        assert mode.id == mode_id


def test_mode_that_include_mode(mode_repo):
    modes = mode_repo.modes_that_include_mode("panacea")
    modes = [m.id for m in modes]
    assert modes == ["panacea", "panacea_links", "karp"]
