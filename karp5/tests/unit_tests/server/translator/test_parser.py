import pytest

from karp5.server.translator import parser
from karp5.config import conf_mgr


def test_make_settings_empty_call():
    settings = parser.make_settings(None, {})

    assert settings["allowed"] is None
    assert settings["mode"] == conf_mgr.app_config.STANDARDMODE
    assert not settings["user_is_authorized"]


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


@pytest.mark.parametrize("authorized", [False, True])
def test_make_settings_set_user_is_authorized(authorized):
    settings = parser.make_settings(None, {}, user_is_authorized=authorized)

    assert settings["user_is_authorized"] == authorized


def test_parse_extra_empty_call(app):
    with app.test_request_context("/query?q=simple||hej"):
        settings = {}
        with pytest.raises(parser.errors.AuthenticationError):
            parser.parse_extra(settings)


def test_parse_extra_unsupported_request_args(app):
    with app.test_request_context("/query?q=simple||hej&invalid=really"):
        settings = {}
        with pytest.raises(parser.errors.QueryError):
            parser.parse_extra(settings)


def test_parse_extra_minimum_successful(app):
    with app.test_request_context("/query?q=simple||hej"):
        settings = {"mode": "karp", "allowed": ["any"]}  # must exist in conf_mgr
        p_extra = parser.parse_extra(settings)

        assert p_extra == {"term": {"lexiconName": "any"}}


def test_construct_exp_empty_call():
    assert parser.construct_exp([]) == ""


def test_parse_empty_call(app):
    with app.test_request_context("/query?q=a"):
        with pytest.raises(parser.errors.AuthenticationError):
            parser.parse()


def test_parse_no_q(app):
    with app.test_request_context("/query"):
        settings = {"mode": "karp", "allowed": ["any"]}
        with pytest.raises(parser.errors.QueryError):
            parser.parse(settings)


def test_parse_q_simple(app):
    text = "hej"
    lexicon = "any"
    with app.test_request_context(f"/query?q=simple||{text}"):
        settings = {"mode": "karp", "allowed": [lexicon]}
        result = parser.parse(settings)
        expected = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {"match": {"_all": {"operator": "and", "query": text}}},
                                    {"match": {"lemma_german": {"boost": 200, "query": text}}},
                                    {
                                        "match": {
                                            "english.lemma_english": {"boost": 100, "query": text}
                                        }
                                    },
                                ]
                            }
                        },
                        {"term": {"lexiconName": "any"}},
                    ]
                }
            }
        }
        assert result == expected

