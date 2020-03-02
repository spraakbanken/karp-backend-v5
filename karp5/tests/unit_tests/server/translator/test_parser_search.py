from karp5.server.translator import parser

from karp5.tests.util import assert_es_search


def test_search_get_context(app):
    exps = [{"match_phrase": {"lexiconName": "panacea"}}]
    with app.test_request_context("/getcontext/panacea"):
        result = parser.search(exps, [], [], usefilter=True, constant_score=False)
    expected = {"query": {"bool": {"must": [{"match_phrase": {"lexiconName": "panacea"}}]}}}
    expected = {"bool": {"must": [{"match_phrase": {"lexiconName": "panacea"}}]}}
    assert_es_search(result, expected)
    assert result == expected


def test_search_get_pre_post(app):
    exps = [
        {"match_phrase": {"lexiconName": "panacea"}},
        {"range": {"lemma_german.raw": {"gte": "Abbau"}}},
    ]
    with app.test_request_context("/getcontext/panacea"):
        result = parser.search(exps, [], [], usefilter=False, constant_score=True)
    expected = {
        "query": {
            "bool": {
                "filter": [
                    {"match_phrase": {"lexiconName": "panacea"}},
                    {"range": {"lemma_german.raw": {"gte": "Abbau"}}},
                ]
            }
        }
    }
    expected = {
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"lexiconName": "panacea"}},
                    {"range": {"lemma_german.raw": {"gte": "Abbau"}}},
                ]
            }
        }
    }
    assert_es_search(result, expected)
    assert result == expected


def test_search_autocomplete_q(app):
    exp = {
        "bool": {
            "should": [
                {"term": {"lemma_german": {"boost": "500", "value": "sig"}}},
                {"match_phrase": {"lemma_german": "sig"}},
                {"match_phrase": {"english.lemma_english": "sig"}},
            ]
        }
    }
    fields = {"exists": {"field": "lemma_german"}}
    resource = {
        "bool": {
            "should": [
                {"term": {"lexiconName": "bar"}},
                {"term": {"lexiconName": "foo"}},
                {"term": {"lexiconName": "large_lex"}},
                {"term": {"lexiconName": "panacea"}},
                {"term": {"lexiconName": "panacea_links"}},
            ]
        }
    }
    exps = [exp, fields, resource]
    filters = []
    fields = ""
    with app.test_request_context("/autocomplete?q=sig"):
        result = parser.search(exps, filters, fields, usefilter=True)
    expected = {
        "query": {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [
                                {"term": {"lemma_german": {"boost": "500", "value": "sig"}}},
                                {"match_phrase": {"lemma_german": "sig"}},
                                {"match_phrase": {"english.lemma_english": "sig"}},
                            ]
                        }
                    },
                    {"exists": {"field": "lemma_german"}},
                    {
                        "bool": {
                            "should": [
                                {"term": {"lexiconName": "bar"}},
                                {"term": {"lexiconName": "foo"}},
                                {"term": {"lexiconName": "large_lex"}},
                                {"term": {"lexiconName": "panacea"}},
                                {"term": {"lexiconName": "panacea_links"}},
                            ]
                        }
                    },
                ]
            }
        }
    }
    expected = {
        "query": {
            "constant_score": {
                "filter": {
                    "bool": {
                        "must": [
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "term": {
                                                "lemma_german": {"boost": "500", "value": "sig"}
                                            }
                                        },
                                        {"match_phrase": {"lemma_german": "sig"}},
                                        {"match_phrase": {"english.lemma_english": "sig"}},
                                    ]
                                }
                            },
                            {"exists": {"field": "lemma_german"}},
                            {
                                "bool": {
                                    "should": [
                                        {"term": {"lexiconName": "bar"}},
                                        {"term": {"lexiconName": "foo"}},
                                        {"term": {"lexiconName": "large_lex"}},
                                        {"term": {"lexiconName": "panacea"}},
                                        {"term": {"lexiconName": "panacea_links"}},
                                    ]
                                }
                            },
                        ]
                    }
                }
            }
        }
    }
    assert_es_search(result, expected)
    assert result == expected

