from karp5.server.translator.parser import freetext


def test_freetext_minimum():
    text = None
    mode = "karp"
    result = freetext(text, mode)

    expected = {
        "query": {
            "bool": {
                "should": [[
                    {"match": {"_all": {"operator": "and", "query": text}}},
                    {"match": {"lemma_german": {"boost": 200, "query": text}}},
                    {"match": {"english.lemma_english": {"boost": 100, "query": text}}}
                    ]
                    ]
            }
        }
    }

    assert result == expected
