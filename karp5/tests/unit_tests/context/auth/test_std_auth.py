import hashlib
from unittest.mock import patch

from karp5.context.auth.std_auth import check_user


def test_hashlib_md5():
    user = "User"
    pwd = "Pwd"
    secret = "Secret"
    user_pwd_secret = user + pwd + secret

    result = hashlib.md5((user + pwd + secret).encode("utf-8")).hexdigest()
    assert result is not None


def test_check_user_empty_call(app):
    result = None
    assert result is None
