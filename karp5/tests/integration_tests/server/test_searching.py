from karp5.server import searching

from karp5.tests.util import get_json

def test_autocomplete_with_q(client_w_panacea):
    result = get_json(client_w_panacea, "autocomplete?q=sig")
    assert result["hits"]["total"] == 0
    #https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?multi=kasta,docka&resource=saldom&mode=external
    #https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?q=kasus&resource=saldom,dalin,hellqvist
    #https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?q=kasta&resource=saldom


def test_getcontext_panacea(client_w_panacea):
    result = get_json(client_w_panacea, "getcontext/panacea")
    center_source = {
        'english': [
            {
                'corpus_prob': 4.89859255463686e-06,
                'lemma_english': 'suppression',
                'package_prob': 0.0,
                'pos_english': 'No',
                'target_prob': 3.8369042032346446e-05
            },
            {
                'corpus_prob': 0.0,
                'lemma_english': 'mining',
                'package_prob': 0.0,
                'pos_english': 'No',
                'target_prob': 0.0
            },
            {
                'corpus_prob': 3.5721305315087224e-05,
                'lemma_english': 'removal',
                'package_prob': 0.1393939393939394,
                'pos_english': 'No',
                'target_prob': 0.0002100906287505403
            },
            {
                'corpus_prob': 7.780117586776189e-06,
                'lemma_english': 'degradation',
                'package_prob': 0.18484848484848485,
                'pos_english': 'No',
                'target_prob': 3.622252219836902e-05
            },
            {
                'corpus_prob': 0.0,
                'lemma_english': 'quarrying',
                'package_prob': 0.0,
                'pos_english': 'No',
                'target_prob': 0.0
            },
            {
                'corpus_prob': 1.6607189268563003e-05,
                'lemma_english': 'breakdown',
                'package_prob': 0.015151515151515152,
                'pos_english': 'No',
                'target_prob': 2.4148348132246012e-05
            },
            {
                'corpus_prob': 0.0001688573668833647,
                'lemma_english': 'reduction',
                'package_prob': 0.6545454545454545,
                'pos_english': 'No',
                'target_prob': 0.0007480621621411321
            },
            {
                'corpus_prob': 0.0,
                'lemma_english': 'dismantling',
                'package_prob': 0.0,
                'pos_english': 'No',
                'target_prob': 0.0
            },
            {
                'corpus_prob': 2.4973216945207523e-07,
                'lemma_english': 'run-down',
                'package_prob': 0.0,
                'pos_english': 'No',
                'target_prob': 0.0
            },
            {
                'corpus_prob': 2.3052200257114636e-07,
                'lemma_english': 'dismantlement',
                'package_prob': 0.006060606060606061,
                'pos_english': 'No',
                'target_prob': 5.366299584943559e-07
            },
            {
                'corpus_prob': 4.89859255463686e-06,
                'lemma_english': 'collapse',
                'package_prob': 0.0,
                'pos_english': 'No',
                'target_prob': 0.00017198990169744105
            }
        ],
        'lemma_german': 'Abbau',
        'lexiconName': 'panacea',
        'lexiconOrder': 0,
        'pos_german': 'No'
    }
    post = []
    pre = []
    assert result["pre"] == pre
    assert result["center"]["_source"] == center_source
    assert result["post"] == post
