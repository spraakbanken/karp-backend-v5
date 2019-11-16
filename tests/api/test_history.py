import time

from tests.util import get_json, post_json


def test_lexicon_history(client_w_panacea):
    query = "/checklexiconhistory/panacea"

    result = get_json(client_w_panacea, query)

    assert result is not None
    assert "resource" in result
    assert result["resource"] == "panacea"
    assert len(result["updates"]) == 0


def test_update(client_w_foo):
    query = "query?q=simple||one&mode=foo"

    result = get_json(client_w_foo, query)

    assert result is not None
    assert "hits" in result
    assert "hits" in result["hits"]
    hits = result["hits"]["hits"]
    assert len(hits) > 0

    entry = {
        "lexiconName": "foo",
        "lexiconOrder": 2,
        "foo": "five"
    }

    new_data = post_json(
        client_w_foo,
        "/add/foo",
        {'doc': entry}
    )
    assert "sql_loaded" in new_data
    assert new_data["sql_loaded"] == 1
    assert "es_loaded" in new_data
    assert new_data["es_loaded"] == 1
    assert "es_ans" in new_data
    new_id = new_data["es_ans"]["_id"]
    time.sleep(1)
    for i in range(2, 10):
        changed_entry = entry.copy()
        changed_entry['foo'] = entry['foo'] * i
        data = post_json(
            client_w_foo,
            f"/mkupdate/foo/{new_id}",
            {
                'doc': changed_entry,
                'message': 'changes',
                'version': i - 1
            }
        )
        time.sleep(1)

    result = get_json(client_w_foo, f"/checkhistory/foo/{new_id}")
    assert result is not None
    assert "updates" in result
    assert len(result["updates"]) == 10

    result = get_json(client_w_foo, f"/checkdifference/foo/{new_id}/latest")

    assert "diff" in result
    assert "field" in result["diff"][0]

