from karp5.domain.models.user import User


def test_empty_user():
    user = User()

    assert not user.is_authenticated
    assert user.is_not_authenticated()
    assert user.allowed_lexicons == []
    assert user.name == ""
