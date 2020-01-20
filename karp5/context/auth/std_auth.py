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

    postdata = {"include_open_resources": "true"}
    server = conf_mgr.app_config.AUTH_RESOURCES
    user, pw = "", ""
    if auth is not None:
        # if the user has provided log in details, check them against
        # the auth server. Otherwise only the open list of open resources will
        # be provided
        try:
            user, pw = auth.username, auth.password
        except TypeError:
            raise errors.KarpAuthenticationError(
                "Incorrect username or password.", "Make sure that they are properly encoded",
            )
        postdata["username"] = user
        postdata["password"] = pw
        secret = conf_mgr.app_config.AUTH_SECRET
        postdata["checksum"] = hashlib.md5(user + pw + secret).hexdigest()
        server = conf_mgr.app_config.AUTH_SERVER

    try:
        _logger.debug("Auth server: " + server)
        postdata = urllib.parse.urlencode(postdata)
        postdata = postdata.encode("ascii")
        contents = urlopen(server, postdata).read()
        # _logger.debug("Auth answer: "+str(contents))
        auth_response = json.loads(contents)
    except HTTPError as e:
        _logger.error(e)
        raise errors.KarpAuthenticationError("Could not contact authentication server.")
    except ValueError:
        raise errors.KarpAuthenticationError("Invalid response from authentication server.")
    except Exception as e:
        _logger.error(e)
        raise errors.KarpAuthenticationError("Unexpected error during authentication.")

    lexitems = auth_response.get("permitted_resources", {})
    session["lexicon_list"] = lexitems.get("lexica", {})
    session["username"] = user
    session["authenticated"] = auth_response["authenticated"]
    return {
        "auth_response": auth_response,
        "username": user,
        "lexicon_list": lexitems.get("lexica", {}),
        "authenticated": auth_response["authenticated"],
    }
