from unittest.mock import patch

import pytest

from karp5.context.auth import validate_user


@pytest.fixture
def check_user_response_valid_user():
    response = {
        "authenticated": True,
        "lexicon_list": {
            "open": {"read": True, "write": False, "admin": False},
            "closed": {"read": False, "write": False, "admin": False},
            "write": {"read": True, "write": True, "admin": False},
            "admin": {"read": True, "write": True, "admin": True},
        },
    }
    return response


@pytest.mark.parametrize(
    "mode,facit",
    [("read", ["open", "write", "admin"]), ("write", ["write", "admin"]), ("admin", ["admin"])],
)
def test_validate_user_valid_user(mode, facit, check_user_response_valid_user):
    with patch("karp5.context.auth.check_user") as check_user_mock:
        check_user_mock.return_value = check_user_response_valid_user
        authenticated, allowed_lexicons = validate_user(mode=mode)
        check_user_mock.assert_called_with()

        assert authenticated
        for lexicon in facit:
            assert lexicon in allowed_lexicons

        assert "closed" not in allowed_lexicons
