from flask import request, session
from json import loads
import md5
import logging
import karp5.server.errorhandler as eh
import karp5.server.helper.configmanager as configM
import urllib
from urllib2 import urlopen, HTTPError


_logger = logging.getLogger('karp5')


def check_user(force_lookup=False):
    """Authenticates a user against an authentication server.
       Returns a dictionary with permitted resources for the user
    """
    # Logged in, just return the lexicon list
    if not force_lookup and 'username' in session:
        _logger.debug('user has %s' % session)
        return session

    # If there is no session for this user, check with the auth server
    auth = request.authorization

    postdata = {"include_open_resources": "true"}
    server = configM.config['AUTH']['AUTH_RESOURCES']
    user, pw = "", ''
    if auth is not None:
        # if the user has provided log in details, check them against
        # the auth server. Otherwise only the open list of open resources will
        # be provided
        try:
            user, pw = auth.username, auth.password
        except TypeError:
            raise eh.KarpAuthenticationError("Incorrect username or password.",
                                             "Make sure that they are properly encoded")
        postdata["username"] = user
        postdata["password"] = pw
        secret = configM.config['AUTH']['AUTH_SECRET']
        postdata["checksum"] = md5.new(user + pw + secret).hexdigest()
        server = configM.config['AUTH']['AUTH_SERVER']

    try:
        _logger.debug("Auth server: " + server)
        contents = urlopen(server, urllib.urlencode(postdata)).read()
        # _logger.debug("Auth answer: "+str(contents))
        auth_response = loads(contents)
    except HTTPError as e:
        _logger.error(e)
        raise eh.KarpAuthenticationError("Could not contact authentication server.")
    except ValueError:
        raise eh.KarpAuthenticationError("Invalid response from authentication server.")
    except Exception as e:
        _logger.error(e)
        raise eh.KarpAuthenticationError("Unexpected error during authentication.")

    lexitems = auth_response.get("permitted_resources", {})
    session['lexicon_list'] = lexitems.get("lexica", {})
    session['username'] = user
    session['authenticated'] = auth_response['authenticated']
    return {"auth_response": auth_response, "username": user,
            "lexicon_list": lexitems.get("lexica", {}),
            "authenticated": auth_response['authenticated']}


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
        return auth.get('authenticated'), auth.get("auth_response")

    user_auth = check_user()
    auth_response = user_auth['authenticated']

    allowed = []
    for lex, val in user_auth['lexicon_list'].items():
        if val[mode]:
            allowed.append(lex)

    return auth_response, allowed
