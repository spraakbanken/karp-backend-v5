import datetime
import io
import json
import time

import pytest

from karp5.cli import upload_offline

from karp5.tests.util import get_json, post_json


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

    entry = {"lexiconName": "foo", "lexiconOrder": 2, "foo": "five"}

    new_data = post_json(client_w_foo, "/add/foo", {"doc": entry, "message": "adding entry"})
    assert "sql_loaded" in new_data
    assert new_data["sql_loaded"] == 1
    assert "es_loaded" in new_data
    assert new_data["es_loaded"] == 1
    assert "es_ans" in new_data
    new_id = new_data["es_ans"]["_id"]
    time.sleep(1)
    for i in range(2, 10):
        changed_entry = entry.copy()
        changed_entry["foo"] = entry["foo"] * i
        data = post_json(
            client_w_foo,
            f"/mkupdate/foo/{new_id}",
            {"doc": changed_entry, "message": "changes", "version": i - 1},
        )
        assert data is not None
        time.sleep(1)

    time.sleep(1)
    result = get_json(client_w_foo, f"/checkhistory/foo/{new_id}")
    assert result is not None
    assert "updates" in result
    print(f"result = {result}")
    # TODO This test fails.
    assert len(result["updates"]) > 0

    result = get_json(client_w_foo, f"/checkdifference/foo/{new_id}/latest")

    assert "diff" in result
    assert "field" in result["diff"][0]


def test_print_latestversion_foo(cli_w_foo):
    fp = io.StringIO()
    upload_offline.printlatestversion("foo", fp=fp)

    data = json.loads(fp.getvalue())

    print(f"data = {data}")
    assert len(data) == 5


def test_print_latestversion_panacea(cli_w_panacea):
    fp = io.StringIO()
    upload_offline.printlatestversion("panacea", fp=fp)

    data = json.loads(fp.getvalue())

    # print(f"data = {data}")
    assert len(data) == 6609


def test_export_latestversion_foo(cli_w_foo):
    fp = io.StringIO()
    upload_offline.printlatestversion("foo", fp=fp, with_id=True)

    data = json.loads(fp.getvalue())

    print(f"data = {data}")
    assert len(data) == 5
    assert "_id" in data[0]
    assert "_source" in data[0]


def test_export_latestversion_panacea(cli_w_panacea):
    fp = io.StringIO()
    upload_offline.printlatestversion("panacea", fp=fp, with_id=True)

    data = json.loads(fp.getvalue())

    # print(f"data = {data}")
    assert len(data) == 6609
    assert "_id" in data[0]
    assert "_source" in data[0]
