from unittest import mock

import pytest

from karp5.server import searching


def test_autocompletequery(app):
    mode = "foo"
    q = "any"
    boost = {"term": {"field": {"boost": "500", "value": q}}}

    result = searching.autocompletequery(mode, boost, q)

    expected = {"bool": {"should": [boost, {"match_phrase": {"foo": q}}]}}

    assert result == expected


def test_autocomplete_foo_no_user(app):
    q = "any"
    mode = "foo"
    path = f"/autocomplete?q={q}&mode={mode}"
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.server.translator.parser.adapt_query", return_value=None
        ) as adapt_query_mock, mock.patch(
            "karp5.config.conf_mgr.elastic", return_value="ES"
        ), mock.patch(
            "karp5.context.auth.validate_user", return_value=(False, ["foo"])
        ):
            searching.autocomplete()
            expected_elasticq = {
                "query": {
                    "constant_score": {
                        "filter": {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {"term": {"foo": {"boost": "500", "value": "any"}}},
                                                {"match_phrase": {"foo": "any"}},
                                            ]
                                        }
                                    },
                                    {"exists": {"field": "foo"}},
                                    {"term": {"lexiconName": "foo"}},
                                    {"term": {"status": "ok"}},
                                ]
                            }
                        }
                    }
                }
            }
            adapt_query_mock.assert_called_with(
                1000, 0, "ES", expected_elasticq, {"size": 1000, "index": mode, "_source": [mode]}
            )


def test_autocomplete_foo_w_user(app):
    q = "any"
    mode = "foo"
    path = f"/autocomplete?q={q}&mode={mode}"
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.server.translator.parser.adapt_query", return_value=None
        ) as adapt_query_mock, mock.patch(
            "karp5.config.conf_mgr.elastic", return_value="ES"
        ), mock.patch(
            "karp5.context.auth.validate_user", return_value=(True, ["foo"])
        ):
            searching.autocomplete()
            expected_elasticq = {
                "query": {
                    "constant_score": {
                        "filter": {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {"term": {"foo": {"boost": "500", "value": "any"}}},
                                                {"match_phrase": {"foo": "any"}},
                                            ]
                                        }
                                    },
                                    {"exists": {"field": "foo"}},
                                    {"term": {"lexiconName": "foo"}},
                                ]
                            }
                        }
                    }
                }
            }
            adapt_query_mock.assert_called_with(
                1000, 0, "ES", expected_elasticq, {"size": 1000, "index": mode, "_source": [mode]}
            )


def test_get_context_foo_no_user_no_center(app):
    lexicon = "foo"
    path = f"/getcontext/{lexicon}"
    center_q_hits = {"hits": {"hits": [{"sort": ["key"], "_id": "test"}]}}
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.config.conf_mgr.elastic"
        ) as conf_mgr_elastic_mock, mock.patch(
            "karp5.context.auth.validate_user", return_value=(False, ["foo"])
        ), mock.patch(
            "karp5.server.searching.get_pre_post", return_value=[None]
        ):
            attrs = {"search.return_value": center_q_hits}
            es_search_mock = mock.Mock()
            es_search_mock.configure_mock(**attrs)
            conf_mgr_elastic_mock.return_value = es_search_mock

            searching.get_context(lexicon)

            expected_center_q = {
                "query": {
                    "bool": {
                        "must": [
                            {"match_phrase": {"lexiconName": lexicon}},
                            {"term": {"status": "ok"}},
                        ],
                    }
                }
            }
            es_search_mock.search.assert_called_with(
                index=lexicon,
                doc_type="lexicalentry",
                size=1,
                body=expected_center_q,
                sort=["foo.raw:asc"],
            )


def test_get_context_foo_w_user_no_center(app):
    lexicon = "foo"
    path = f"/getcontext/{lexicon}"
    center_q_hits = {"hits": {"hits": [{"sort": ["key"], "_id": "test"}]}}
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.config.conf_mgr.elastic"
        ) as conf_mgr_elastic_mock, mock.patch(
            "karp5.context.auth.validate_user", return_value=(True, ["foo"])
        ), mock.patch(
            "karp5.server.searching.get_pre_post", return_value=[None]
        ):
            attrs = {"search.return_value": center_q_hits}
            es_search_mock = mock.Mock()
            es_search_mock.configure_mock(**attrs)
            conf_mgr_elastic_mock.return_value = es_search_mock

            searching.get_context(lexicon)

            expected_center_q = {
                "query": {"bool": {"must": [{"match_phrase": {"lexiconName": lexicon}},],}}
            }
            es_search_mock.search.assert_called_with(
                index=lexicon,
                doc_type="lexicalentry",
                size=1,
                body=expected_center_q,
                sort=["foo.raw:asc"],
            )


def test_get_context_foo_no_user_w_center(app):
    lexicon = "foo"
    center_id = "TEST1"
    path = f"/getcontext/{lexicon}?center={center_id}"
    center_q_hits = {"hits": {"hits": [{"sort": ["key"], "_id": "test"}]}}
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.config.conf_mgr.elastic"
        ) as conf_mgr_elastic_mock, mock.patch(
            "karp5.context.auth.validate_user", return_value=(False, ["foo"])
        ), mock.patch(
            "karp5.server.searching.get_pre_post", return_value=[None]
        ):
            attrs = {"search.return_value": center_q_hits}
            es_search_mock = mock.Mock()
            es_search_mock.configure_mock(**attrs)
            conf_mgr_elastic_mock.return_value = es_search_mock

            searching.get_context(lexicon)

            expected_center_q = {
                "query": {
                    "bool": {
                        "must": {"term": {"_id": center_id}},
                        "filter": [{"term": {"status": "ok"}}],
                    }
                }
            }
            es_search_mock.search.assert_called_with(
                index=lexicon,
                doc_type="lexicalentry",
                size=1,
                body=expected_center_q,
                sort=["foo.raw:asc"],
            )


def test_get_context_foo_w_user_w_center(app):
    lexicon = "foo"
    center_id = "TEST1"
    path = f"/getcontext/{lexicon}?center={center_id}"
    center_q_hits = {"hits": {"hits": [{"sort": ["key"], "_id": "test"}]}}
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.config.conf_mgr.elastic"
        ) as conf_mgr_elastic_mock, mock.patch(
            "karp5.context.auth.validate_user", return_value=(True, ["foo"])
        ), mock.patch(
            "karp5.server.searching.get_pre_post", return_value=[None]
        ):
            attrs = {"search.return_value": center_q_hits}
            es_search_mock = mock.Mock()
            es_search_mock.configure_mock(**attrs)
            conf_mgr_elastic_mock.return_value = es_search_mock

            searching.get_context(lexicon)

            expected_center_q = {
                "query": {"term": {"_id": center_id}},
            }
            es_search_mock.search.assert_called_with(
                index=lexicon,
                doc_type="lexicalentry",
                size=1,
                body=expected_center_q,
                sort=["foo.raw:asc"],
            )


def test_get_pre_post_foo_w_user(app):
    q = "any"
    mode = "foo"
    path = f"/autocomplete?q={q}&mode={mode}"
    exps = []
    center_id = None
    sortfield = []
    sortfieldname = "foo"
    sortvalue = None
    origentry_sort = None
    size = 10
    settings = {"size": size}
    es = "ES"
    place = "post"
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.server.translator.parser.adapt_query", return_value={}
        ) as adapt_query_mock, mock.patch(
            "karp5.config.conf_mgr.elastic", return_value="ES"
        ), mock.patch(
            "karp5.context.auth.validate_user", return_value=(True, ["foo"])
        ):
            searching.get_pre_post(
                exps,
                center_id,
                sortfield,
                sortfieldname,
                sortvalue,
                origentry_sort,
                mode,
                settings,
                es,
                mode,
                place=place,
            )
            expected_elasticq = {"query": {"bool": {"must": [{"range": {"foo": {"gte": "None"}}}]}}}
            expected_size = 3 * size + 3
            adapt_query_mock.assert_called_with(
                expected_size,
                0,
                es,
                expected_elasticq,
                {
                    "size": expected_size,
                    "from_": 0,
                    "sort": sortfield,
                    "index": mode,
                    "_source": ["lexiconName", mode],
                },
            )


def test_get_pre_post_foo_no_user(app):
    q = "any"
    mode = "foo"
    path = f"/autocomplete?q={q}&mode={mode}"
    exps = []
    center_id = None
    sortfield = []
    sortfieldname = "foo"
    sortvalue = None
    origentry_sort = None
    size = 10
    settings = {"size": size}
    es = "ES"
    place = "post"
    filters = [{"term": {"status": "ok"}}]
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.server.translator.parser.adapt_query", return_value={}
        ) as adapt_query_mock, mock.patch(
            "karp5.config.conf_mgr.elastic", return_value="ES"
        ), mock.patch(
            "karp5.context.auth.validate_user", return_value=(True, ["foo"])
        ):
            searching.get_pre_post(
                exps,
                center_id,
                sortfield,
                sortfieldname,
                sortvalue,
                origentry_sort,
                mode,
                settings,
                es,
                mode,
                place=place,
                filters=filters,
            )
            expected_elasticq = {
                "bool": {
                    "must": [{"range": {"foo": {"gte": "None"}}}],
                    "filter": {"bool": {"must": filters}},
                }
            }
            expected_size = 3 * size + 3
            adapt_query_mock.assert_called_with(
                expected_size,
                0,
                es,
                expected_elasticq,
                {
                    "size": expected_size,
                    "from_": 0,
                    "sort": sortfield,
                    "index": mode,
                    "_source": ["lexiconName", mode],
                },
            )


def test_export_foo_unauth_user(app):
    lexicon = "foo"
    path = f"/export/{lexicon}"
    with app.test_request_context(path):
        with mock.patch("karp5.context.auth.validate_user", return_value=(False, ["foo"])):
            with pytest.raises(searching.errors.KarpAuthenticationError):
                searching.export(lexicon)


def test_export_foo_lexicon_not_permitted(app):
    lexicon = "restricted"
    path = f"/export/{lexicon}"
    with app.test_request_context(path):
        with mock.patch("karp5.context.auth.validate_user", return_value=(False, ["permitted"])):
            with pytest.raises(searching.errors.KarpAuthenticationError):
                searching.export(lexicon)
