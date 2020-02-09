from karp5.server.translator import parser


def test_search_get_context(app):
    exps = [{'match_phrase': {'lexiconName':      'panacea'}}]
    with app.test_request_context("/getcontext/panacea"):
        result = parser.search(exps, [], [], usefilter=True, constant_score=False)
    expected = {'bool': {'must':                  [{'match_phrase': {'lexiconName': 'panacea'}}]}}
    assert result == expected


def test_search_autocomplete_q(app):
    exp = {
        "bool": {
            "should": [
                {
                    "term": {
                        "lemma_german": {
                            "boost": "500",
                            "value": "sig"
                        }
                    }
                },
                {
                    "match_phrase": {
                        "lemma_german": "sig"
                    }
                },
                {
                    "match_phrase": {
                        "english.lemma_english": "sig"
                    }
                }
            ]
        }
    }
    fields = {"exists": {"field": "lemma_german"}}
    resource = {
        'bool': {
            'should': [
                {
                    'term': {
                        'lexiconName': 'bar'
                    }
                },
                {
                    'term': {
                        'lexiconName': 'foo'
                    }
                },
                            {'term': {'lexiconName': 'large_lex'}},
                            {'term': {'lexiconName': 'panacea'}},
                            {'term': {'lexiconName': 'panacea_links'}}
                        ]
                    }}
    exps = [exp, fields, resource]
    filters = []
    fields = ""
    with app.test_request_context("/autocomplete?q=sig"):
        result = parser.search(exps, filters, fields, usefilter=True)
    expected = {
        'query': {
        'constant_score': {
        'filter': {
            'bool': {
                'must': [
                    {'bool': {
                        'should': [
                            {'term': {'lemma_german': {'boost': '500', 'value':      'sig'}}},
                            {'match_phrase': {'lemma_german': 'sig'}},
                            {'match_phrase': {'english.lemma_english': 'sig'}}
                        ]
                    }},
                    {'exists': {'field': 'lemma_german'}},
                    {'bool': {
                        'should': [
                            {'term': {'lexiconName': 'bar'}},
                            {'term': {'lexiconName': 'foo'}},
                            {'term': {'lexiconName': 'large_lex'}},
                            {'term': {'lexiconName': 'panacea'}},
                            {'term': {'lexiconName': 'panacea_links'}}
                        ]
                    }}
                ]
                }
            }
        }
        }
        }
    assert result == expected
