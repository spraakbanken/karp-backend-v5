import base64
import hashlib
from unittest.mock import patch, Mock

from karp5.context.auth import std_auth  # pytype: disable=import-error
from karp5.config import conf_mgr


def test_hashlib_md5():
    user = "User"
    pwd = "Pwd"
    secret = "Secret"
    user_pwd_secret = user + pwd + secret

    result = hashlib.md5((user + pwd + secret).encode("utf-8")).hexdigest()
    assert result is not None


def test_check_user_no_user(app):
    with app.test_request_context("/query?q=simple||hej"):
        with patch("karp5.context.auth.std_auth.make_auth_request") as mk_auth_req_mock:
            mk_auth_req_mock.return_value = {
                "authenticated": False,
            }
            result = std_auth.check_user()
            mk_auth_req_mock.assert_called_with(
                conf_mgr.app_config.AUTH_RESOURCES, {"include_open_resources": "true"}
            )
            assert "username" in result
            assert result["username"] == ""


def test_check_user_valid_user(app):
    with patch("karp5.context.auth.std_auth.make_auth_request") as mk_auth_req_mock:
        username = "valid_user"
        password = "pwd"
        creds = base64.b64encode(b"valid_user:pwd").decode("utf-8")
        with app.test_request_context(
            "/query?q=simple||hej", headers={"Authorization": "Basic " + creds}
        ):
            mk_auth_req_mock.return_value = {
                "authenticated": True,
                "permitted_resources": {
                    "lexica": {"a": {"read": True, "write": True, "admin": True}}
                },
            }
            result = std_auth.check_user()
            mk_auth_req_mock.assert_called_with(
                conf_mgr.app_config.AUTH_SERVER,
                {
                    "include_open_resources": "true",
                    "username": username,
                    "password": password,
                    "checksum": "84f0163c1b904d544dd0e1d9168bd58b",
                },
            )
            assert "username" in result
            assert result["username"] == username
            assert result["authenticated"]
            assert "lexicon_list" in result
            assert "a" in result["lexicon_list"]
            assert isinstance(result["lexicon_list"]["a"], dict)
            assert "auth_response" in result


def test_check_user_invalid_user(app):
    with patch("karp5.context.auth.std_auth.make_auth_request") as mk_auth_req_mock:
        username = "invalid_user"
        password = "pwd"
        creds = base64.b64encode(b"invalid_user:pwd").decode("utf-8")
        with app.test_request_context(
            "/query?q=simple||hej", headers={"Authorization": "Basic " + creds}
        ):
            mk_auth_req_mock.return_value = {
                "authenticated": False,
                "permitted_resources": {
                    "lexica": {"open": {"read": True, "write": False, "admin": False}}
                },
            }
            result = std_auth.check_user()
            mk_auth_req_mock.assert_called_with(
                conf_mgr.app_config.AUTH_SERVER,
                {
                    "include_open_resources": "true",
                    "username": username,
                    "password": password,
                    "checksum": "8832a3ca67946278bcc74e138cd0718d",
                },
            )
            assert "username" in result
            assert result["username"] == username
            assert not result["authenticated"]
            assert "lexicon_list" in result
            assert "open" in result["lexicon_list"]
            assert isinstance(result["lexicon_list"]["open"], dict)
            assert result["lexicon_list"]["open"]["read"]
            assert not result["lexicon_list"]["open"]["write"]
            assert not result["lexicon_list"]["open"]["admin"]
            assert "auth_response" in result
