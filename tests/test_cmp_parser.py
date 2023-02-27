import pytest

from karp5.server.translator import parser as v5_parser
from karp.server.translator import parser as v4_parser



@pytest.fixture()
def mode() -> str:
    return "karp"


@pytest.fixture()
def query_string(mode: str) -> str:
    return f"mode={mode}"


def test_make_settings():
    permitted = []
    v4_settings = v4_parser.make_settings(permitted, {"size": 1000, "mode": "external"})
    v5_settings = v5_parser.make_settings(permitted, {"size": 1000}, user_is_authorized=True)

    assert v4_settings["size"] == v5_settings["size"]


def test_get_mode(query_string: str, mode: str):
    # v5_mode = v5_parser.get_mode()
    v4_mode = v4_parser.get_mode(query_string)

    assert v4_mode == mode
    
