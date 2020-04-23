from unittest import mock

import pytest

from karp5.server.translator.validatejson import validate_json


def test_validate_json_escapes_correct():
    lexicon_id = "Test"
    doc = {"field": "&", "string": "o\u0308"}
    expected = {"field": "&amp;", "string": "ö"}

    validate_json(doc, lexicon_id)

    assert doc == expected


def test_validate_json_respect_no_escape_but_normalizes_string():
    lexicon_id = "test"
    doc = {"field": "&", "string": "o\u0308"}
    expected = {"field": "&", "string": "ö"}

    with mock.patch(
        "karp5.server.translator.validatejson.conf_mgr", lexicons={"test": {"no_escape": True}}
    ):
        validate_json(doc, lexicon_id)

    assert doc == expected


@pytest.mark.parametrize(
    "doc, expected",
    [
        ({"xml": "<tag>"}, {"xml": "<tag>"}),
        ({"xml": "[<tag>]"}, {"xml": "[<tag>]"}),
        ({"xml": {"text": "<tag>"}}, {"xml": {"text": "&lt;tag&gt;"}}),
    ],
)
def test_validate_json_handles_xml_correct_with_escaping(doc, expected):
    lexicon_id = "test"

    with mock.patch(
        "karp5.server.translator.validatejson.conf_mgr", lexicons={"test": {"usedtags": ["tag"]}}
    ):
        validate_json(doc, lexicon_id)

    assert doc == expected


@pytest.mark.parametrize(
    "doc, expected",
    [
        ({"xml": "<tag>"}, {"xml": "<tag>"}),
        ({"xml": "[<tag>]"}, {"xml": "[<tag>]"}),
        ({"xml": {"text": "<tag>"}}, {"xml": {"text": "<tag>"}}),
    ],
)
def test_validate_json_handles_xml_correct_without_escaping(doc, expected):
    lexicon_id = "test"

    with mock.patch(
        "karp5.server.translator.validatejson.conf_mgr",
        lexicons={"test": {"no_escape": True, "usedtags": ["tag"]}},
    ):
        validate_json(doc, lexicon_id)

    assert doc == expected
