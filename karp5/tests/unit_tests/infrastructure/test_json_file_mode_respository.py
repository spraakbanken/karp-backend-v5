from pathlib import Path
from karp5.infrastructure.json_file_mode_repository import JsonFileModeRepository


def test_json_file_mode_repository():
    repo = JsonFileModeRepository(config_dir=Path("karp5/tests/data/config"))

    assert repo.mode_ids() == ["panacea", "panacea_links", "karp", "foo", "large_lex"]

    for mode_id in repo.mode_ids():
        mode = repo.mode_by_id(mode_id)

        assert mode.id == mode_id
