from unittest import mock

from karp5.dbhandler.dbhandler import SQLNull, get_entries_to_keep_gen


def test_sql_null_w_lexicon():
    sql_null = SQLNull("LEXICON")
    assert str(sql_null) == "SQLNull: No SQL db available for LEXICON"
    assert sql_null.message == "No SQL db available for LEXICON"


def test_get_entries_to_keep_gen():
    lexicon = "foo"
    entries = [
        {"id": 1, "value": "expected", "status": "added"},
    ]

    with mock.patch(
            "karp5.dbhandler.dbhandler.dbselect_gen", return_value=entries
        ), mock.patch(
            "karp5.dbhandler.dbhandler.get_engine", return_value=("ENGINE", "DBENTRY"
        )):
        for entry in get_entries_to_keep_gen(lexicon):
            assert entry["value"] == "expected"
