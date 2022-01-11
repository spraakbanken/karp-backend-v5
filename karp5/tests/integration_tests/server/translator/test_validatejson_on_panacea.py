import collections.abc
import copy
import json

from karp5.server.translator.validatejson import escape, validate_json


def test_validate_json_on_panacea(app):
    file_name = "karp5/tests/data/data/panacea/panacea.json"
    lexicon_id = "panacea"

    with open(file_name) as fp:
        objs = json.load(fp)
        for obj in objs:
            orig = copy.deepcopy(obj)
            validate_json(obj, lexicon_id)
            compare(orig, obj)


def compare(orig, obj):
    assert type(orig) == type(obj)

    if isinstance(orig, str):
        # check that strings are escaped but otherwise unchanged
        assert escape(orig) == obj
        return

    if isinstance(orig, collections.abc.Sized):
        # all other types of objects should have unchanged length
        assert len(orig) == len(obj)

    # recursively check the rest
    if isinstance(orig, dict):
        for key, val in orig.items():
            compare(val, obj[key])
    elif isinstance(orig, list):
        for i, val in enumerate(orig):
            compare(val, obj[i])
    else:
        assert orig == obj
