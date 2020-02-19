from karp5.server import searching

from karp5.tests.util import get_json


def test_autocomplete_with_q(client_w_panacea):
    result = get_json(client_w_panacea, "autocomplete?q=sig")
    assert result["hits"]["total"] == 0
    # https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?multi=kasta,docka&resource=saldom&mode=external
    # https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?q=kasus&resource=saldom,dalin,hellqvist
    # https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?q=kasta&resource=saldom


def test_getcontext_panacea(client_w_panacea):
    result = get_json(client_w_panacea, "getcontext/panacea")
    center_source = {
        "english": [
            {
                "corpus_prob": 4.89859255463686e-06,
                "lemma_english": "suppression",
                "package_prob": 0.0,
                "pos_english": "No",
                "target_prob": 3.8369042032346446e-05,
            },
            {
                "corpus_prob": 0.0,
                "lemma_english": "mining",
                "package_prob": 0.0,
                "pos_english": "No",
                "target_prob": 0.0,
            },
            {
                "corpus_prob": 3.5721305315087224e-05,
                "lemma_english": "removal",
                "package_prob": 0.1393939393939394,
                "pos_english": "No",
                "target_prob": 0.0002100906287505403,
            },
            {
                "corpus_prob": 7.780117586776189e-06,
                "lemma_english": "degradation",
                "package_prob": 0.18484848484848485,
                "pos_english": "No",
                "target_prob": 3.622252219836902e-05,
            },
            {
                "corpus_prob": 0.0,
                "lemma_english": "quarrying",
                "package_prob": 0.0,
                "pos_english": "No",
                "target_prob": 0.0,
            },
            {
                "corpus_prob": 1.6607189268563003e-05,
                "lemma_english": "breakdown",
                "package_prob": 0.015151515151515152,
                "pos_english": "No",
                "target_prob": 2.4148348132246012e-05,
            },
            {
                "corpus_prob": 0.0001688573668833647,
                "lemma_english": "reduction",
                "package_prob": 0.6545454545454545,
                "pos_english": "No",
                "target_prob": 0.0007480621621411321,
            },
            {
                "corpus_prob": 0.0,
                "lemma_english": "dismantling",
                "package_prob": 0.0,
                "pos_english": "No",
                "target_prob": 0.0,
            },
            {
                "corpus_prob": 2.4973216945207523e-07,
                "lemma_english": "run-down",
                "package_prob": 0.0,
                "pos_english": "No",
                "target_prob": 0.0,
            },
            {
                "corpus_prob": 2.3052200257114636e-07,
                "lemma_english": "dismantlement",
                "package_prob": 0.006060606060606061,
                "pos_english": "No",
                "target_prob": 5.366299584943559e-07,
            },
            {
                "corpus_prob": 4.89859255463686e-06,
                "lemma_english": "collapse",
                "package_prob": 0.0,
                "pos_english": "No",
                "target_prob": 0.00017198990169744105,
            },
        ],
        "lemma_german": "Abbau",
        "lexiconName": "panacea",
        "lexiconOrder": 0,
        "pos_german": "No",
    }
    post = [
        {
            "_id": "qLsaOXABkxee4U0WZNC1",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [{"lemma_english": "image"}, {"lemma_english": "copy"}],
                "lemma_german": "Abbild",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abbild"],
        },
        {
            "_id": "yrsaOXABkxee4U0WZdFo",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [
                    {"lemma_english": "figure"},
                    {"lemma_english": "projection"},
                    {"lemma_english": "illustration"},
                    {"lemma_english": "image"},
                    {"lemma_english": "mapping"},
                ],
                "lemma_german": "Abbildung",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abbildung"],
        },
        {
            "_id": "-bsaOXABkxee4U0WYMj7",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [
                    {"lemma_english": "termination"},
                    {"lemma_english": "disconnection"},
                    {"lemma_english": "demolition"},
                    {"lemma_english": "abortion"},
                    {"lemma_english": "breaking-off"},
                    {"lemma_english": "abort"},
                ],
                "lemma_german": "Abbruch",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abbruch"],
        },
        {
            "_id": "V7saOXABkxee4U0WXsJb",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [
                    {"lemma_english": "cover"},
                    {"lemma_english": "coverage"},
                    {"lemma_english": "covering"},
                ],
                "lemma_german": "Abdeckung",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abdeckung"],
        },
        {
            "_id": "lbsaOXABkxee4U0WZM4c",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [
                    {"lemma_english": "imprint"},
                    {"lemma_english": "impression"},
                    {"lemma_english": "printing"},
                    {"lemma_english": "print"},
                    {"lemma_english": "copy"},
                ],
                "lemma_german": "Abdruck",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abdruck"],
        },
        {
            "_id": "LbsaOXABkxee4U0WYMZl",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [{"lemma_english": "dinner"}, {"lemma_english": "supper"}],
                "lemma_german": "Abendessen",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abendessen"],
        },
        {
            "_id": "ebsaOXABkxee4U0WX8SF",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [
                    {"lemma_english": "adventure"},
                    {"lemma_english": "affair"},
                    {"lemma_english": "venture"},
                ],
                "lemma_german": "Abenteuer",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abenteuer"],
        },
        {
            "_id": "AbsaOXABkxee4U0WXMHw",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [{"lemma_english": "deprivation"}, {"lemma_english": "denial"}],
                "lemma_german": "Aberkennung",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Aberkennung"],
        },
        {
            "_id": "-7saOXABkxee4U0WZdJp",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [
                    {"lemma_english": "refuse"},
                    {"lemma_english": "waste"},
                    {"lemma_english": "offal"},
                    {"lemma_english": "rubbish"},
                    {"lemma_english": "drop"},
                    {"lemma_english": "trash"},
                    {"lemma_english": "litter"},
                    {"lemma_english": "scrap"},
                    {"lemma_english": "discard"},
                    {"lemma_english": "garbage"},
                    {"lemma_english": "release"},
                ],
                "lemma_german": "Abfall",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abfall"],
        },
        {
            "_id": "KLsaOXABkxee4U0WWb_M",
            "_index": "panacea_test_upload_02",
            "_score": None,
            "_source": {
                "english": [{"lemma_english": "intercept"}, {"lemma_english": "interception"}],
                "lemma_german": "Abfangen",
                "lexiconName": "panacea",
            },
            "_type": "lexicalentry",
            "sort": ["Abfangen"],
        },
    ]
    pre = []
    assert result["pre"] == pre
    assert result["center"]["_source"] == center_source
    for post_entry, expected in zip(result["post"], post):
        assert post_entry["_source"] == expected["_source"]
