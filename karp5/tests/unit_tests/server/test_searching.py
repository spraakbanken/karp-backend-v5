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


@pytest.mark.parametrize("user_is_authorized", [False, True])
def test_autocomplete_foo(app, user_is_authorized):
    q = "any"
    mode = "foo"
    path = f"/autocomplete?q={q}&mode={mode}"
    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.server.translator.parser.adapt_query", return_value=None
        ) as adapt_query_mock, mock.patch(
            "karp5.config.conf_mgr.elastic", return_value="ES"
        ), mock.patch(
            "karp5.context.auth.validate_user", return_value=(user_is_authorized, ["foo"])
        ):
            searching.autocomplete()
            expected_must = [
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
            if not user_is_authorized:
                expected_must.append({"term": {"status": "ok"}})
            expected_elasticq = {
                "query": {
                    "constant_score": {
                        "filter": {
                            "bool": {
                                "must": expected_must
                            }
                        }
                    }
                }
            }
            adapt_query_mock.assert_called_with(
                1000, 0, "ES", expected_elasticq, {"size": 1000, "index": mode, "_source": [mode]}
            )


@pytest.mark.parametrize("lexicon", ["foo"])
@pytest.mark.parametrize("user_is_authorized", [False, True])
@pytest.mark.parametrize("with_center", [False, True])
def test_get_context(app, lexicon, user_is_authorized, with_center):
    center_id = "ID_TEST"
    if with_center:
        path = f"/getcontext/{lexicon}?center={center_id}"
    else:
        path = f"/getcontext/{lexicon}"
    sortvalue = "KEY_TEST"
    center_q_hits = {"hits": {"hits": [{"sort": [sortvalue], "_id": center_id}]}}

    with app.test_request_context(path):
        with mock.patch("karp5.server.searching.jsonify", return_value=None), mock.patch(
            "karp5.config.conf_mgr.elastic"
        ) as conf_mgr_elastic_mock, mock.patch(
            "karp5.context.auth.validate_user", return_value=(user_is_authorized, [lexicon]),
        ), mock.patch(
            "karp5.server.searching.get_pre_post", return_value=[None]
        ) as get_pre_post_mock:
            attrs = {"search.return_value": center_q_hits}
            es_search_mock = mock.Mock()
            es_search_mock.configure_mock(**attrs)
            conf_mgr_elastic_mock.return_value = es_search_mock

            searching.get_context(lexicon)
            if with_center:
                expected_q = {"term": {"_id": center_id}}
            else:
                expected_q = {"match_phrase": {"lexiconName": lexicon}}
            if user_is_authorized:
                expected_filters = []
            else:
                expected_filters = [{"term": {"status": "ok"}}]

            if with_center:
                if user_is_authorized:
                    expected_center_q = {"query": expected_q}
                else:
                    expected_center_q = {
                        "query": {"bool": {"must": expected_q, "filter": expected_filters}}
                    }
            else:
                if user_is_authorized:
                    expected_center_q = {"query": {"bool": {"must": [expected_q],}}}
                else:
                    expected_center_q = {
                        "query": {"bool": {"must": [expected_q, expected_filters[0],],}}
                    }

            es_search_mock.search.assert_called_with(
                index=lexicon,
                doc_type="lexicalentry",
                size=1,
                body=expected_center_q,
                sort=["foo.raw:asc"],
            )

            assert get_pre_post_mock.call_count == 2

            for call_args in get_pre_post_mock.call_args_list:
                print(f"call_args = {call_args}")
                args, kwargs = call_args
                assert "place" in kwargs
                assert "filters" in kwargs
                assert kwargs["filters"] == expected_filters
                assert isinstance(args[6], int)


@pytest.mark.parametrize("place", ["post", "pre"])
@pytest.mark.parametrize("user_is_authorized", [False, True])
def test_get_pre_post_foo(app, place, user_is_authorized):
    mode = "foo"
    exps = []
    center_id = None
    sortfield = ["SORTFIELD_TEST"]
    sortfieldname = "foo"  # must exist in config
    sortvalue = "SORTVALUE_TEST"
    size = 10
    es = "ES"
    if user_is_authorized:
        filters = []
    else:
        filters = [{"term": {"status": "ok"}}]
    with mock.patch(
        "karp5.server.translator.parser.adapt_query", return_value={}
    ) as adapt_query_mock:
        searching.get_pre_post(
            exps,
            center_id,
            sortfield,
            sortfieldname,
            sortvalue,
            mode,
            size,
            es,
            mode,
            place=place,
            filters=filters,
        )
        expected_q = {"range": {sortfieldname: {"gte" if place == "post" else "lte": sortvalue}}}
        if user_is_authorized:
            expected_elasticq = {"query": {"bool": {"must": [expected_q]}}}
        else:
            expected_elasticq = {
                "bool": {"must": [expected_q], "filter": {"bool": {"must": filters}},}
            }
        expected_size = 3 * (size + 1)
        expected_sort = ["{}:{}".format(sortfield[0], "asc" if place == "post" else "desc")]

        adapt_query_mock.assert_called_once()
        args, _ = adapt_query_mock.call_args
        assert args[0] == expected_size
        assert args[3] == expected_elasticq
        assert args[4]["size"] == expected_size
        assert args[4]["sort"] == expected_sort


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
