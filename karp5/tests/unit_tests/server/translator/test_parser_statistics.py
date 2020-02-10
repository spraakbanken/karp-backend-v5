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
    #s = es_dsl.Search.from_dict(expected_q)

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
    expected_q = {
        'aggs': {
            'q_statistics': {
                'aggs': {
                    'lexiconOrder': {
                        'aggs': {
                            'lexiconName': {
                                'terms': {
                                    'field': 'lexiconName',
                                    'shard_size': 27000,
                                    'size': 1000
                                }
                            }
                        },
                        'terms': {
                            'field': 'lexiconOrder',
                            'shard_size': 27000,
                            'size': 1000
                        }
                    }
                },
                'filter': {
                    'bool': {
                        'must': [
                            {
                                'exists': {
                                    'field': 'pos_german'
                                }
                            },
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
                                            'term':{
                                                'lexiconName': 'panacea_links'
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
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
    es_expected_q = es_dsl.Search.from_dict(expected_q)
    assert count_q == expected_q
    assert more == expected_more
    es_count_q = es_dsl.Search.from_dict(count_q)
    assert es_count_q == es_expected_q
