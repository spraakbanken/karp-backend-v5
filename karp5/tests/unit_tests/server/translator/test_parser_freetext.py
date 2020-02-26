from karp5.server.translator.parser import freetext

from karp5.tests.util import assert_es_search


def test_freetext_minimum():
    text = None
    mode = "karp"
    result = freetext(text, mode)

    expected = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"_all": {"operator": "and", "query": text}}},
                    {"match": {"lemma_german": {"boost": 200, "query": text}}},
                    {"match": {"english.lemma_english": {"boost": 100, "query": text}}},
                ]
            }
        }
    }
    assert_es_search(result, expected)

    assert result == expected


def test_freetext_with_extra():
    text = None
    mode = "karp"
    extra = {"term": {"extra": "extra"}}
    result = freetext(text, mode, extra=extra)

    expected = {
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {"match": {"_all": {"operator": "and", "query": text}}},
                                {"match": {"lemma_german": {"boost": 200, "query": text}}},
                                {"match": {"english.lemma_english": {"boost": 100, "query": text}}},
                            ]
                        }
                    },
                    extra,
                ]
            }
        }
    }
    assert_es_search(result, expected)

    assert result == expected


def test_freetext_with_filters():
    text = None
    mode = "karp"
    filters = [{"term": {"extra": "extra"}}]
    result = freetext(text, mode, filters=filters)

    expected = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"_all": {"operator": "and", "query": text}}},
                    {"match": {"lemma_german": {"boost": 200, "query": text}}},
                    {"match": {"english.lemma_english": {"boost": 100, "query": text}}},
                ],
                "filter": filters[0],
            }
        }
    }

    assert_es_search(result, expected)
    assert result == expected

