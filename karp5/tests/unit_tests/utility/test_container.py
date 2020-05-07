import pytest

from karp5.utility.container import merge_dict


def test_merge_dict_with_disjoint_keys():
    adict = {"a": 1}
    bdict = {"b": 2}

    merge_dict(adict, bdict)

    assert adict["a"] == 1
    assert adict["b"] == 2


@pytest.mark.parametrize("a_val,b_val,expected", [
    (1, 2, [1, 2]),
    ("ab", "ba", ["ab", "ba"]),
    ("abc", "abc", "abc"),
    (["a"], ["b"], ["a", "b"]),
    (["a"], ["a"], ["a"]),
    ("a", ["b"], ["a", "b"]),
    ("a", ["a"], ["a"]),
    (["a"], "b", ["a", "b"]),
    (["a"], "a", ["a"]),
])
def test_merge_dict_with_joint_keys(a_val, b_val, expected):
    adict = {"a": a_val}
    bdict = {"a": b_val}

    merge_dict(adict, bdict)

    assert adict["a"] == expected
