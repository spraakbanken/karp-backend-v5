from unittest import mock
import typing

from karp5.dbhandler.dbhandler import SQLNull, get_entries_to_keep_gen


def test_sql_null_w_lexicon():
    sql_null = SQLNull("LEXICON")
    assert str(sql_null) == "SQLNull: No SQL db available for LEXICON"
    assert sql_null.message == "No SQL db available for LEXICON"


def generate_from_list(
    l: typing.List[typing.Dict[str, typing.Any]]
) -> typing.Generator[typing.Dict[str, typing.Any], None, None]:
    for obj in l:
        yield obj


def test_get_entries_to_keep_gen():
    lexicon = "foo"
    entries = [
        {"id": 1, "value": "expected", "status": "updated"},
        {"id": 1, "value": "not expected", "status": "added"},
        {"id": 2, "value": "not expected", "status": "removed"},
        {"id": 3, "value": "expected", "status": "added"},
        {"id": 3, "value": "not expected", "status": "removed"},
    ]

    with mock.patch(
        "karp5.dbhandler.dbhandler.dbselect_gen", return_value=generate_from_list(entries)
    ), mock.patch("karp5.dbhandler.dbhandler.get_engine", return_value=("ENGINE", "DBENTRY")):
        for entry in get_entries_to_keep_gen(lexicon):
            assert entry["value"] == "expected"
