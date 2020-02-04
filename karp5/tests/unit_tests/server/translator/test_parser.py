import pytest

from karp5.server.translator import parser
from karp5.config import conf_mgr


def test_make_settings_empty_call():
    settings = parser.make_settings(None, {})

    assert settings["allowed"] is None
    assert settings["mode"] == conf_mgr.app_config.STANDARDMODE


def test_make_settings_append_field():
    settings = parser.make_settings(None, {"extra": "added"})

    assert settings["allowed"] is None
    assert settings["mode"] == conf_mgr.app_config.STANDARDMODE
    assert "extra" in settings
    assert settings["extra"] == "added"


def test_make_settings_change_mode():
    settings = parser.make_settings(None, {"mode": "new"})

    assert settings["allowed"] is None
    assert settings["mode"] == "new"


def test_parse_extra_empty_call(app):
    with app.test_request_context("/query?q=simple||hej"):
        settings = {}
        with pytest.raises(parser.errors.AuthenticationError):
            parser.parse_extra(settings)


def test_parse_extra_minimum_successful(app):
    with app.test_request_context("/query?q=simple||hej"):
        settings = {
            "mode": "karp",  # must exist in conf_mgr
            "allowed": ["any"]
        }
        p_extra = parser.parse_extra(settings)

        assert p_extra == {"term": {"lexiconName": "any"}}
