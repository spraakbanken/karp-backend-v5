from builtins import str
from datetime import timedelta
import logging
import six
from elasticsearch import ConnectionError
from flask import make_response, request, current_app
from functools import update_wrapper

from karp5 import errors
from karp5.config import mgr as conf_mgr
import karp5.server.update as update
from karp5.dbhandler import emailsender as email


_logger = logging.getLogger("karp5")


# Decorator for allowing cross site http request etc.
# http://flask.pocoo.org/snippets/56/
def crossdomain(
    origin=None,
    methods=None,
    headers=None,
    max_age=21600,
    attach_to_all=True,
    automatic_options=True,
):
    if methods is not None:
        methods = ", ".join(sorted(x.upper() for x in methods))
    if headers is None:
        # Set standard headers here
        # TODO figure out which ones that are meaningful (when)
        headers = ["Content-Type", "Authorization"]
    if headers is not None and not isinstance(headers, six.string_types):
        headers = ", ".join(x.upper() for x in headers)
    if not isinstance(origin, six.string_types):
        origin = ", ".join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers["allow"]

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == "OPTIONS":
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != "OPTIONS":
                return resp

            h = resp.headers

            h["Access-Control-Allow-Origin"] = origin
            h["Access-Control-Allow-Methods"] = get_methods()
            h["Access-Control-Max-Age"] = str(max_age)
            if headers is not None:
                h["Access-Control-Allow-Headers"] = headers
            return resp

        f.provide_automatic_options = False
        f.required_methods = ["OPTIONS"]
        return update_wrapper(wrapped_function, f)

    return decorator


def register(app, initiator):
    urls = []

    def route(url="", methods=None, crossdomain=True, name=None):
        """ Decorator function @route
            Adds the function to a list of urls, which should later be processed
            by Flask (see flaskhelper.py)
            If 'name' is not given, the url will be the name of the function.
            If 'url', it will appended to the function name, and may contain variable
            parts of the path
            'methods' is a list of allowed methods, defaults to 'GET'
            Example:
            @route()
            def mypage():
               return render_page("hello")
            ==> /mypage

            @route('<pagename>')
            def mypage(pagename=''):
               return render_page("welcome to"+pagename)
            ==> /mypage/any_page_name
        """

        def f(func):
            if name is not None:
                urlname = name
            elif url:
                urlname = "/%s/%s" % (func.__name__, url)
            else:
                urlname = "/%s" % func.__name__
            _logger.debug("add url\n\n")
            urls.append((urlname, func, methods, crossdomain))
            return func

        return f

    initiator(route)
    for url, func, methods, cross in urls:
        if cross:
            # add the crossdomain decorator to the view function
            func = crossdomain(origin="*", methods=methods)(func)
        app.add_url_rule(url, endpoint=url, view_func=func, methods=methods)


# TODO test if error handling works. If not: move the decorator to top level
# Error handling, show all KarpExceptions to the client
def init_errorhandler(app):
    @app.errorhandler(Exception)
    @crossdomain(origin="*")
    def handle_invalid_usage(error):
        try:
            request.get_data()
            data = request.data
            data = data.decode("utf8")
            auth = request.authorization
            e_type = "Predicted" if isinstance(error, errors.KarpException) else "Unpredicted"

            _logger.debug("Error on url %s" % request.full_path)
            user = "unknown"
            if auth:
                user = auth.username
            # s = '%s: %s  User: %s\n\t%s: %s\n\t%s\n' \
            #     % (datetime.datetime.now(), request.path, user, e_type,
            #        str(error), data)
            s = "%s  User: %s\n%s: %s\n%s\n" % (
                request.full_path,
                user,
                e_type,
                error.message,
                data,
            )
            _logger.exception(s)

            if isinstance(error, ConnectionError):
                _logger.debug(update.handle_update_error(error, data, user, ""))

            if isinstance(error, errors.KarpException):
                # Log full error message if available
                if error.debug_msg:
                    _logger.debug(error.debug_msg)

                status_code = error.status_code
                if error.user_msg:
                    return str(error.user_msg), status_code
                else:
                    return error.message, status_code

            else:
                _logger.exception(error.message)
                return "Oops, something went wrong\n", 500

        except Exception:
            # In case of write conflicts etc, print to anoter file
            # and send email to admin
            import time
            import traceback

            logdir = conf_mgr.app_config.LOG_DIR
            trace = traceback.format_exc()
            date = time.strftime("%Y-%m-%d %H:%M:%S")
            msg = "Cannot print log file: %s, %s" % (date, trace)
            title = "Karp urgent logging error"
            if conf_mgr.app_config.ADMIN_EMAILS:

                email.send_notification(conf_mgr.app_config.ADMIN_EMAILS, title, msg)
            open(logdir + "KARPERR" + time.strftime("%Y%m%d"), "a").write(msg)
            return "Oops, something went wrong\n", 500
