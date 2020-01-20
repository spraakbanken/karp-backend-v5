import logging

_logger = logging.getLogger("karp5")

check_user = None
validate_user = None


def init(auth_name: str):
    global check_user, validate_user
    if auth_name == "dummy":
        _logger.warning("Using dummy auth module.")
        from karp5.context.auth import dummy_auth

        check_user = dummy_auth.check_user
        validate_user = dummy_auth.validate_user
    else:
        from karp5.context.auth import std_auth

        check_user = std_auth.check_user
        validate_user = std_auth.validate_user
