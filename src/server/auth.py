from flask import request, session
from json import loads
import md5
import logging
import src.server.errorhandler as eh
import src.server.helper.configmanager as configM
import urllib
from urllib2 import urlopen, HTTPError


def check_user(force_lookup=False):
    """Authenticates a user against an authentication server.
       Returns a dictionary with permitted resources for the user
    """

    return {"auth_response": {}, "username": 'malin',
            #"lexicon_list": {"term-swefin": {"read": True, "write": True}},
            "lexicon_list": { "ao": { "admin": False, "read": True, "write": False }, "aventinus": { "admin": False, "read": True, "write": False }, "blingbring": { "admin": False, "read": True, "write": False }, "bliss": { "admin": False, "read": True, "write": False }, "blisschar": { "admin": True, "read": True, "write": True }, "blissword": { "admin": True, "read": True, "write": True }, "bring": { "admin": False, "read": True, "write": False }, "dalin": { "admin": False, "read": True, "write": False }, "dalin-base": { "admin": False, "read": True, "write": False }, "dalin-mfl": { "admin": True, "read": True, "write": True }, "dalinm": { "admin": False, "read": True, "write": False }, "diapivot": { "admin": False, "read": True, "write": False }, "fgnp": { "admin": True, "read": True, "write": True }, "fsv-mfl": { "admin": True, "read": True, "write": True }, "fsvm": { "admin": False, "read": True, "write": False }, "hellqvist": { "admin": True, "read": True, "write": True }, "kelly": { "admin": True, "read": True, "write": True }, "konstruktikon": { "admin": True, "read": True, "write": True }, "konstruktikon-multi": { "admin": True, "read": True, "write": True }, "konstruktikon-rus": { "admin": True, "read": True, "write": True }, "laerka": { "admin": True, "read": True, "write": True }, "langfn": { "admin": True, "read": True, "write": True }, "lexin": { "admin": False, "read": True, "write": False }, "lsilex": { "admin": True, "read": True, "write": True }, "lwt": { "admin": True, "read": True, "write": True }, "lwt-pwn": { "admin": False, "read": True, "write": False }, "neo-idiom": { "admin": False, "read": True, "write": False }, "osa": { "admin": False, "read": True, "write": False }, "panacea": { "admin": True, "read": True, "write": True }, "parolelex": { "admin": False, "read": True, "write": False }, "parolelexplus": { "admin": True, "read": True, "write": True }, "saldo": { "admin": False, "read": True, "write": False }, "saldoe": { "admin": False, "read": True, "write": False }, "saldom": { "admin": False, "read": True, "write": False }, "saol": { "admin": True, "read": True, "write": True }, "schlyter": { "admin": False, "read": True, "write": False }, "sentimentlex": { "admin": True, "read": True, "write": True }, "simple": { "admin": False, "read": True, "write": False }, "simpleplus": { "admin": True, "read": True, "write": True }, "skbl": { "admin": True, "read": True, "write": True }, "soederwall": { "admin": False, "read": True, "write": False }, "soederwall-supp": { "admin": False, "read": True, "write": False }, "sol-articles": { "admin": True, "read": True, "write": True }, "sol-contributors": { "admin": True, "read": True, "write": True }, "sol-works": { "admin": True, "read": True, "write": True }, "sporting": { "admin": False, "read": True, "write": False }, "swedberg": { "admin": False, "read": True, "write": False }, "swedberg-mfl": { "admin": True, "read": True, "write": True }, "swedbergm": { "admin": False, "read": True, "write": False }, "swefn": { "admin": True, "read": True, "write": True }, "swesaurus": { "admin": False, "read": True, "write": False }, "swo": { "admin": True, "read": True, "write": True }, "term-finswe": { "admin": True, "read": True, "write": True }, "term-swefin": { "admin": True, "read": True, "write": True }, "termin": { "admin": False, "read": True, "write": False }, "test": { "admin": True, "read": True, "write": True }, "vocation-list": { "admin": False, "read": True, "write": False }, "wordnet-saldo": { "admin": True, "read": True, "write": True } },

            "authenticated": True}
    # Logged in, just return the lexicon list
    if not force_lookup and 'username' in session:
        logging.debug('user has %s' % session)
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
        logging.debug("Auth server: " + server)
        contents = urlopen(server, urllib.urlencode(postdata)).read()
        # logging.debug("Auth answer: "+str(contents))
        auth_response = loads(contents)
    except HTTPError as e:
        logging.error(e)
        raise eh.KarpAuthenticationError("Could not contact authentication server.")
    except ValueError:
        raise eh.KarpAuthenticationError("Invalid response from authentication server.")
    except Exception as e:
        logging.error(e)
        raise eh.KarpAuthenticationError("Unexpected error during authentication.")

    lexitems = auth_response.get("permitted_resources", {})
    session['lexicon_list'] = lexitems.get("lexica", {})
    session['username'] = user
    session['authenticated'] = auth_response['authenticated']

    return {"auth_response": auth_response, "username": user,
            "lexicon_list": lexitems.get("lexica", {}),
            "authenticated": auth_response['authenticated']}


def validate_user(force_user="", mode="write"):
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
    user = user_auth['username']

    if (auth_response or not user) and (not force_user or user == force_user):
        allowed = []
        for lex, val in user_auth['lexicon_list'].items():
            if val[mode]:
                allowed.append(lex)

        return auth_response, allowed

    return auth_response, []
