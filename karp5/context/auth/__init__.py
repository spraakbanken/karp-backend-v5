import logging

_logger = logging.getLogger("karp5")

check_user = None


def validate_user(mode="write"):
    """Authenticates a user against an authentication server.
       Returns a dictionary with permitted resources for the user
    """
    # If mode is read and no user info is provided, just get all open lexicons
    # if mode is read and user info is provided, return all lexicons that may
    # be seen by this user
    # if mode is not read, do as before
    # new auth has Lexicon in uppercase, singular

    if mode == "verbose":
        auth = check_user(force_lookup=True)
        return auth.get("authenticated"), auth.get("auth_response")

    user_auth = check_user()
    auth_response = user_auth["authenticated"]

    allowed = []
    for lex, val in user_auth["lexicon_list"].items():
        if val[mode]:
            allowed.append(lex)

    return auth_response, allowed


def init(auth_name: str):
    global check_user
    if auth_name == "dummy":
        _logger.warning("Using dummy auth module.")
        from karp5.context.auth import dummy_auth

        check_user = dummy_auth.check_user
    else:
        from karp5.context.auth import std_auth

        check_user = std_auth.check_user
