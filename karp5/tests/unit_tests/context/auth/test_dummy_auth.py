import pytest

from karp5.context.auth import dummy_auth  # pytype: disable=import-error

from karp5.tests.util import mk_headers


def test_check_user_w_no_user(app):
    with app.test_request_context("/"):
        result = dummy_auth.check_user()

    assert result["authenticated"]
    assert result["username"] == "TestUser"

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            assert val


def test_check_user_w_user(app):
    username = "valid_user"
    headers = mk_headers(username)
    with app.test_request_context("/", headers=headers):
        result = dummy_auth.check_user()

    assert result["username"] == username
    assert result["authenticated"]

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            assert val


def test_check_user_w_invalid_user(app):
    username = "invalid"
    headers = mk_headers(username)
    with app.test_request_context("/", headers=headers):
        result = dummy_auth.check_user()

    assert result["username"] == username
    assert not result["authenticated"]

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            assert not val


def test_check_user_w_read_rights(app):
    username = "read"
    headers = mk_headers(username)
    with app.test_request_context("/", headers=headers):
        result = dummy_auth.check_user()

    assert result["username"] == username
    assert result["authenticated"]

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            if key == "read":
                assert val
            else:
                assert not val


def test_check_user_w_write_rights(app):
    username = "write"
    headers = mk_headers(username)
    with app.test_request_context("/", headers=headers):
        result = dummy_auth.check_user()

    assert result["username"] == username
    assert result["authenticated"]

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            if key in ["read", "write"]:
                assert val
            else:
                assert not val


@pytest.mark.parametrize("lexicon", ["foo"])
def test_check_user_w_invalid_user_w_lex(app, lexicon):
    username = "invalid"
    headers = mk_headers(f"{username}__{lexicon}")
    with app.test_request_context("/", headers=headers):
        result = dummy_auth.check_user()

    assert result["username"] == username
    assert not result["authenticated"]

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            if lex == lexicon:
                assert not val
            elif key == "read":
                assert val
            else:
                assert not val


@pytest.mark.parametrize("lexicon", ["foo"])
@pytest.mark.parametrize("username", ["read", "write", "admin"])
def test_check_user_w_user_w_lex(app, lexicon, username):
    headers = mk_headers(f"{username}__{lexicon}")
    with app.test_request_context("/", headers=headers):
        result = dummy_auth.check_user()

    ok_keys = ["read"]
    if username == "write":
        ok_keys.append("write")
    if username == "admin":
        ok_keys.append("write")
        ok_keys.append("admin")
    assert result["username"] == username
    assert result["authenticated"]

    for lex, rights in result["lexicon_list"].items():
        for key, val in rights.items():
            assert key in ["read", "write", "admin"]
            if lex == lexicon and key in ok_keys:
                assert val
            else:
                assert not val
