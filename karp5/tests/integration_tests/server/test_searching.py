from karp5.server import searching

from karp5.tests.util import get_json

def test_autocomplete_with_q(client_w_panacea):
    result = get_json(client_w_panacea, "autocomplete?q=sig")
    assert result is None
    #https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?multi=kasta,docka&resource=saldom&mode=external
    #https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?q=kasus&resource=saldom,dalin,hellqvist
    #https://ws.spraakbanken.gu.se/ws/karp/v5/autocomplete?q=kasta&resource=saldom


def test_getcontext_panacea(client_w_panacea):
    result = get_json(client_w_panacea, "getcontext/panacea")
    assert result is None
