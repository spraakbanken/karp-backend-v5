"""Handle user authentication.
"""
import json  # noqa: E402
import hashlib  # noqa: E402
import logging  # noqa: E402

from urllib.request import urlopen  # noqa: E402
from urllib.error import HTTPError  # noqa: E402
import urllib.parse  # noqa: E402


from flask import request, session  # noqa: E402

from karp5 import errors  # noqa: E402
from karp5.config import mgr as conf_mgr  # noqa: E402


_logger = logging.getLogger("karp5")


def check_user(force_lookup=False):
    """Authenticates a user against an authentication server.
       Returns a dictionary with permitted resources for the user
    """
    # Logged in, just return the lexicon list
    if not force_lookup and "username" in session:
        _logger.debug("user has %s" % session)
        return session

    # If there is no session for this user, check with the auth server
    auth = request.authorization

    user = "TestUser"
    if auth is not None:
        # if the user has provided log in details, check them against
        # the auth server. Otherwise only the open list of open resources will
        # be provided
        try:
            user, _ = auth.username, auth.password
        except TypeError:
            raise errors.KarpAuthenticationError(
                "Incorrect username or password.", "Make sure that they are properly encoded",
            )
    user_parts = user.split("__")
    if len(user_parts) > 1:
        user = user_parts[0]
        user_lex = user_parts[1]
    else:
        user_lex = None
    lexlist = {}

    for name, val in conf_mgr.lexicons.items():
        if user_lex:
            lexlist[name] = {"read": False, "write": False, "admin": False}
            if name == user_lex:
                if user == "read":
                    lexlist[name] = {"read": True, "write": False, "admin": False}
                elif user == "write":
                    lexlist[name] = {"read": True, "write": True, "admin": False}
                elif user == "admin":
                    lexlist[name] = {"read": True, "write": True, "admin": True}
            elif name != user_lex and user == "invalid":
                lexlist[name] = {"read": True, "write": False, "admin": False}
        else:
            if user == "invalid":
                lexlist[name] = {"read": False, "write": False, "admin": False}
            elif user == "read":
                lexlist[name] = {"read": True, "write": False, "admin": False}
            elif user == "write":
                lexlist[name] = {"read": True, "write": True, "admin": False}
            else:
                lexlist[name] = {"read": True, "write": True, "admin": True}

    print("lexlist = {}".format(lexlist))

    auth_response = {
        "permitted_resources": {"lexica": lexlist},
        "username": user,
        "authenticated": user != "invalid",
    }
    authenticated = user != "invalid"

    lexitems = auth_response.get("permitted_resources", {})
    session["lexicon_list"] = lexlist
    session["username"] = user
    session["authenticated"] = authenticated
    return {
        "auth_response": auth_response,
        "username": user,
        "lexicon_list": lexlist,
        "authenticated": authenticated,
    }

