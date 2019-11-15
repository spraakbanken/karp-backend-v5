from tests.util import get_json


def test_lexicon_history(client_w_panacea):
    query = "/checklexiconhistory/panacea"

    result = get_json(client_w_panacea, query)

    assert result is None

