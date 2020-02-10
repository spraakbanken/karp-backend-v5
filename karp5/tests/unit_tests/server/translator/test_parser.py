import pytest

from karp5.server.translator import parser
from karp5.config import conf_mgr

from karp5.tests.util import assert_es_search


def test_make_settings_empty_call(app):
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
    assert parser.construct_exp(None) == ""


@pytest.mark.parametrize("exps", ["a", "b"])
@pytest.mark.parametrize("querytype", ["filter", "must", "q"])
@pytest.mark.parametrize("constant_score", [True, False])
def test_construct_exp_string(exps, querytype, constant_score):
    result = parser.construct_exp(exps, querytype, constant_score)
    expected = {querytype: {"constant_score": exps} if constant_score else exps}
    assert result == expected


@pytest.mark.parametrize("exps", [["a", "b"]])
@pytest.mark.parametrize("querytype", ["filter", "must", "q"])
@pytest.mark.parametrize("constant_score", [True, False])
def test_construct_exp_list(exps, querytype, constant_score):
    result = parser.construct_exp(exps, querytype, constant_score)
    expected = {"must": exps}
    if querytype != "must":
        expected = {querytype: {"bool": expected}}
    assert result == expected


def test_parse_empty_call(app):
    with app.test_request_context("/query?q=a"):
        with pytest.raises(parser.errors.AuthenticationError):
            parser.parse()


def test_parse_no_q(app):
    with app.test_request_context("/query"):
        settings = {"mode": "karp", "allowed": ["any"]}
        with pytest.raises(parser.errors.QueryError):
            parser.parse(settings)


def test_parse_q_simple_mode_karp(app):
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
        assert_es_search(result, expected)
        assert result == expected


def test_parse_q_simple_mode_foo_no_user(app):
    text = "hej"
    lexicon = "any"
    with app.test_request_context(f"/query?q=simple||{text}"):
        settings = {"mode": "foo", "allowed": [lexicon]}
        result = parser.parse(settings)
        expected = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {"match": {"_all": {"operator": "and", "query": text}}},
                                    {"match": {"foo": {"boost": 100, "query": text}}},
                                ]
                            }
                        },
                        {"term": {"lexiconName": "any"}},
                    ],
                    "filter": {
                        "term": {
                            "status": "ok"
                        }
                    }
                }
            }
        }
        assert_es_search(result, expected)
        assert result == expected


def test_search_empty_input():
    exps = None
    filters = None
    fields = None

    result = parser.search(exps, filters, fields)

    expected = {}

    assert_es_search(result, expected)
    assert result == expected


def test_search_autocomplete():
    pass


# @pytest.mark.parametrize("exps,filters", [
#     ({"match": {"field": "value"}},  {"term": {"status": "ok"}}),
# ])
# @pytest.mark.parametrize("constant_score", (True, False))
# def test_search_case1_dict(exps, filters, constant_score):
#     fields = None
#     isfilter = False
#     highlight = False
#     usefilter = True
#
#     result = parser.search(
#         exps,
#         filters,
#         fields,
#         isfilter,
#         highlight,
#         usefilter,
#         constant_score
#     )
#     if constant_score:
#         expected = {'query': {"bool": {'filter': exps + filters}}}
#     else:
#         expected = {"query": {"bool": {"filter": filters, "must": exps}}}
#
#     assert result == expected


@pytest.mark.parametrize("exps,filters", [
    ([{"match": {"field": "value"}}], [{"term": {"status": "ok"}}]),
])
@pytest.mark.parametrize("constant_score", (True, False))
def test_search_case1(exps, filters, constant_score):
    fields = None
    isfilter = False
    highlight = False
    usefilter = True

    result = parser.search(
        exps,
        filters,
        fields,
        isfilter,
        highlight,
        usefilter,
        constant_score
    )
    if constant_score:
        expected = {"query": {'bool': {"filter": exps + filters}}}
    else:
        expected = {'query': {"bool": {'filter': filters, 'must': exps}}}

    assert_es_search(result, expected)
    assert result == expected


# @pytest.mark.parametrize("exps,filters", [
#     ([{"match": {"field": "value"}}], [{"term": {"status": "ok"}}]),
# ])
# def test_search_case1_list_no_constant_score(exps, filters):
#     fields = None
#     isfilter = False
#     highlight = False
#     usefilter = True
#     constant_score = False
#
#     result = parser.search(
#         exps,
#         filters,
#         fields,
#         isfilter,
#         highlight,
#         usefilter,
#         constant_score
#     )
#
#     expected = {'query': {"bool": {'filter': filters, 'must': exps}}}
#
#     assert result == expected


@pytest.mark.parametrize("usefilter", [True, False])
def test_search_case2_string(usefilter):
    exps = "a"
    filters = "b"
    fields = None
    isfilter = True
    highlight = False
    constant_score = True

    result = parser.search(
        exps,
        filters,
        fields,
        isfilter,
        highlight,
        usefilter,
        constant_score
    )

    expected = {"query": {"bool": {"filter": exps + filters}}}

    assert_es_search(result, expected)
    assert result == expected


@pytest.mark.parametrize("exps", [
    ([{"match": {"field": "value"}}]),
])
@pytest.mark.parametrize("filters", [
    ([{"term": {"status": "ok"}}]),
])
@pytest.mark.parametrize("usefilter", [True, False])
@pytest.mark.parametrize("constant_score", [True, False])
def test_search_case2_list(exps, filters, usefilter, constant_score):
    fields = None
    isfilter = True
    highlight = False

    result = parser.search(
        exps,
        filters,
        fields,
        isfilter,
        highlight,
        usefilter,
        constant_score
    )

    expected = {"query": {"bool": {"filter": exps + filters}}}
    assert_es_search(result, expected)

    assert result == expected


# def test_search_case3_dict():
#     exps = {"match": {"field": "value"}}
#     filters = {"term": {"status": "ok"}}
#     fields = None
#     isfilter = False
#     highlight = False
#     usefilter = False
#     constant_score = True
#
#     result = parser.search(
#         exps,
#         filters,
#         fields,
#         isfilter,
#         highlight,
#         usefilter,
#         constant_score
#     )
#
#     expected = {"query": {"bool": {'filter': {'constant_score': filters}, "must": {"constant_score": exps}}}}
#
#     assert result == expected


def test_search_case3_list():
    exps = [{"match": {"field": "value"}}]
    filters = [{"term": {"status": "ok"}}]
    fields = None
    isfilter = False
    highlight = False
    usefilter = False
    constant_score = True

    result = parser.search(
        exps,
        filters,
        fields,
        isfilter,
        highlight,
        usefilter,
        constant_score
    )

    expected = {"query": {"bool": {'filter': exps + filters}}}

    assert_es_search(result, expected)
    assert result == expected


def test_search_case3_list_no_constant_score():
    exps = [{"match": {"field": "value"}}]
    filters = [{"term": {"status": "ok"}}]
    fields = None
    isfilter = False
    highlight = False
    usefilter = False
    constant_score = False

    result = parser.search(
        exps,
        filters,
        fields,
        isfilter,
        highlight,
        usefilter,
        constant_score
    )

    expected = {"query": {"bool": {'filter': filters, "must": exps}}}

    assert_es_search(result, expected)
    assert result == expected


@pytest.mark.parametrize("exps,filters", [
    ([{"match": {"field": "value"}}], None),
    (None, [{"term": {"status": "ok"}}]),
])
@pytest.mark.parametrize("constant_score", [True, False])
def test_search_case4(exps, filters, constant_score):
    fields = None
    isfilter = False
    highlight = False
    usefilter = False

    result = parser.search(
        exps,
        filters,
        fields,
        isfilter,
        highlight,
        usefilter,
        constant_score
    )
    if exps:
        expected = {"query": {"bool": {"filter" if constant_score else "must": exps}}}
    else:
        expected = {}

    assert_es_search(result, expected)
    assert result == expected

