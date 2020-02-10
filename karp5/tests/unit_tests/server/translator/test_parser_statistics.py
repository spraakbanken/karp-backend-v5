import pytest

import elasticsearch_dsl as es_dsl

from karp5.server.translator import parser


def test_statistics_empty_call():
    pass


def test_build_es_search():
    expected_q = {
        'aggs': {
            'q_statistics': {
                'aggs': {
                    'lexiconOrder': {
                        'terms': {
                            'field': 'lexiconOrder',
                            'size': 1000,
                            'shard_size': 27000
                        }
                    }
                },
                'aggs': {
                    'lexiconName': {
                        'terms': {
                            'field': 'lexiconName',
                            'size': 1000,
                            'shard_size': 27000
                        }
                    }
                }
            }
        },
        'query': {
            'exists': {
                'field': 'pos_german'
            }
        }
    }
    es_s = es_dsl.Search().filter("exists", field="pos_german")
    q_statistics = es_dsl.A("q_statistics")
    lexiconOrder = es_dsl.A("terms", field="lexiconOrder")
    lexiconOrder.aggs.bucket("lexiconName", es_dsl.A("terms", field="lexiconName"))
    q_statistics.aggs.bucket("lexiconOrder", lexiconOrder)
    es_s.aggs.bucket("q_statistics", q_statistics)
    assert expected_q == es_s.to_dict()
    s = es_dsl.Search.from_dict(expected_q)


def test_es_search_aggs_filter():
    es_dict = {
        "aggs": {
            "name": {
                "terms": {
                    "name": "joe"
                }
            }
        },
        "filter": [
            {"exists": {"field": "surname"}}
            ]
    }
    es_dsl.Search.from_dict(es_dict)


def test_statistics_querycount(app):
    stat_size = 1000
    settings = {
        "buckets": ["lexiconOrder", "lexiconName"],
        "size": stat_size,
        "allowed": [
            "bar",
            "foo",
            "large_lex",
            "panacea",
            "panacea_links"
        ]
    }
    path = "/querycount?q=extended||and|pos|exists&mode=panacea"
    with app.test_request_context(path):
        count_q, more = parser.statistics(
            settings,
            order={"lexiconOrder": ("_key", "asc")},
            show_missing=False,
            force_size=stat_size,
        )

    expected_q = {
        'aggs': {
            'q_statistics': {
                'aggs': {
                    'lexiconOrder': {
                        'terms': {
                            'field': 'lexiconOrder',
                            'size': 1000,
                            'shard_size': 27000
                        },
                        'aggs': {
                            'lexiconName': {
                                'terms': {
                                    'field': 'lexiconName',
                                    'size': 1000,
                                    'shard_size': 27000
                                }
                            }
                        }
                    }
                }
            }
        },
        'query': {
            'bool': {
                'filter': [
                    {
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
                                {
                                    'term': {
                                        'lexiconName': 'large_lex'
                                    }
                                },
                                {
                                    'term': {
                                        'lexiconName': 'panacea'
                                    }
                                },
                                {
                                    'term': {
                                        'lexiconName': 'panacea_links'
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'exists': {
                            'field': 'pos_german'
                        }
                    }
                ]
            }
        }
    }
    expected_more = [
        (
            {
                'aggs': {
                    'more': {
                        'cardinality': {
                            'field': 'lexiconName'
                        }
                    }
                }
            },
            'lexiconName'
        ),
        (
            {
                'aggs': {
                    'more': {
                        'cardinality': {
                            'field': 'lexiconOrder'
                        }
                    }
                }
            },
            'lexiconOrder'
        )
    ]
    es_count_q = es_dsl.Search.from_dict(count_q)
    assert count_q == expected_q
    assert more == expected_more
    es_expected_q = es_dsl.Search.from_dict(expected_q)
    assert es_count_q == es_expected_q
