import base64
import hashlib
from unittest.mock import patch, Mock

from karp5.context.auth.std_auth import check_user
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
            result = check_user()
            mk_auth_req_mock.assert_called_with(
                conf_mgr.app_config.AUTH_RESOURCES,
                { "include_open_resources": "true" }
            )
            assert "username" in result
            assert result["username"] == ""


def test_check_user_valid_user(app):
    with patch("karp5.context.auth.std_auth.make_auth_request") as mk_auth_req_mock:
        creds = base64.b64encode(b"valid_user:pwd").decode("utf-8")
        with app.test_request_context("/query?q=simple||hej", headers={"Authorization": "Basic " + creds}):
            mk_auth_req_mock.return_value = {
                "authenticated": True,
            }
            result = check_user()
            mk_auth_req_mock.assert_called_with(
                conf_mgr.app_config.AUTH_SERVER,
                {
                    "include_open_resources": "true",
                    "username": "valid_user",
                    "password": "pwd",
                    "checksum": hashlib.md5(())
                }
            )
            assert "username" in result
            assert result["username"] == ""
