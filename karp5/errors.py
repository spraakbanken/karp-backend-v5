""" Class for exceptions generated by the backend, the converts, ElasticSearch
    or the auth server.
    Errors of type KarpException will be shown to the user
"""


class KarpException(Exception):
    """ The super class, copied from flask:
        http://flask.pocoo.org/docs/0.10/patterns/apierrors/
    """

    def __init__(self, message, debug_msg=None, status_code=None, user_msg=None, payload=None):
        super().__init__()
        self.message = message
        self.debug_msg = debug_msg or message
        self.user_msg = user_msg
        self.status_code = status_code or 400
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

    def __str__(self):
        return "%s %s" % (self.status_code, self.message)


class KarpAuthenticationError(KarpException):
    """ Used for errors given by the auth server """

    def __init__(self, message, debug_msg=None, status_code=None, payload=None):
        super().__init__(
            "Authentication Exception: " + message,
            debug_msg=debug_msg,
            status_code=status_code or 401,
            payload=payload,
        )


class KarpElasticSearchError(KarpException):
    """ Used for errors given by the elastic search """

    def __init__(self, message, debug_msg=None, status_code=None, payload=None):
        KarpException.__init__(
            self, "Database Exception: " + message, debug_msg, status_code, payload
        )


class KarpDbError(KarpException):
    """ Used for errors given by the sql data base """

    def __init__(self, message, debug_msg=None, status_code=None, payload=None):
        KarpException.__init__(self, "SQL Error: %s" % message, debug_msg, status_code, payload)


class KarpParsingError(KarpException):
    """ Used for parsing errors, given during upload. """

    def __init__(self, message, debug_msg=None, status_code=None, payload=None):
        KarpException.__init__(
            self,
            "Parsing Error (no documents uploaded): %s" % message,
            debug_msg,
            status_code,
            payload,
        )


class KarpQueryError(KarpException):
    """ Used for errors given when trying to parse the query string. """

    def __init__(
        self, message, query=None, debug_msg=None, status_code=None, user_msg=None, payload=None,
    ):
        if query:
            msg = f"Query was '{query}'"
        else:
            msg = "No query."
        super().__init__(
            f"Query Error: {message}. {msg}",
            debug_msg=debug_msg,
            status_code=status_code,
            payload=payload,
            user_msg=user_msg,
        )


class KarpGeneralError(KarpException):
    """
    Used for unspecified errors. The actual error message will
    only be shown in the debug log. The user will just get a generic
    error message (see backend.py)
    """

    # TODO split into meaningful subclasses, some should not be shown to client
    # Note: all General Errors are invisible to client for now

    def __init__(
        self, message, user_msg=None, debug_msg=None, query=None, status_code=None, payload=None,
    ):
        """ message: is shown when exception is raised
            debug_msg: will only be shown in log (level=debug)
            user_msg: will be send to user
        """
        if not message:
            message = "Unknown error."
        if query:
            message = f"Error: {message}. Query was: {query}"
        else:
            message = f"Error: {message}"
        super().__init__(
            message,
            debug_msg=debug_msg,
            status_code=status_code,
            user_msg=user_msg,
            payload=payload,
        )
