from karp5.server.translator.parser import freetext


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

    assert result == expected


def test_freetext_with_extra():
    text = None
    mode = "karp"
    extra = {"extra": "extra"}
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

    assert result == expected


def test_freetext_with_filters():
    text = None
    mode = "karp"
    filters = {"extra": "extra"}
    result = freetext(text, mode, filters=filters)

    expected = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"_all": {"operator": "and", "query": text}}},
                    {"match": {"lemma_german": {"boost": 200, "query": text}}},
                    {"match": {"english.lemma_english": {"boost": 100, "query": text}}},
                ],
                "filter": filters,
            }
        }
    }

    assert result == expected

