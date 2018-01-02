import config.setup as setupconf
from datetime import timedelta
from elasticsearch import ConnectionError
from flask import Flask, jsonify, make_response, request, current_app
from functools import update_wrapper
import src.server.errorhandler as eh
import src.server.helper.configmanager as configM
import src.server.update as update

#app = Flask('backend')
app = Flask(__name__.split('.')[0])

# set the secret key
app.secret_key = setupconf.secret_key


# Decorator for allowing cross site http request etc.
# http://flask.pocoo.org/snippets/56/
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is None:
        # Set standard headers here
        # TODO figure out which ones that are meaningful (when)
        headers = ['Content-Type', 'Authorization']
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        f.required_methods = ['OPTIONS']
        return update_wrapper(wrapped_function, f)
    return decorator


def register(urls):
    for url, func, methods, cross in urls:
        if cross:
            # add the crossdomain decorator to the view function
            func = crossdomain(origin='*', methods=methods)(func)
        app.add_url_rule(url, endpoint=url, view_func=func, methods=methods)


# TODO test if error handling works. If not: move the decorator to top level
# Error handling, show all KarpExceptions to the client
@app.errorhandler(Exception)
@crossdomain(origin='*')
def handle_invalid_usage(error):
    try:
        import logging
        request.get_data()
        data = request.data
        data = data.decode('utf8')
        auth = request.authorization
        e_type = 'Predicted' if isinstance(error, eh.KarpException) else 'Unpredicted'

        logging.debug('Error on url %s' % request.full_path)
        user = 'unknown'
        if auth:
            user = auth.username
        # s = '%s: %s  User: %s\n\t%s: %s\n\t%s\n' \
        #     % (datetime.datetime.now(), request.path, user, e_type,
        #        str(error), data)
        s = '%s  User: %s\n%s: %s\n%s\n' \
            % (request.full_path, user, e_type, error.message, data)
        logging.exception(s)

        if isinstance(error, ConnectionError):
            logging.debug(update.handle_update_error(error, data, user, ''))

        if isinstance(error, eh.KarpException):
            # Log full error message if available
            if error.debug_msg:
                logging.debug(error.debug_msg)

            # KarpGeneralError is handled differently
            if isinstance(error, eh.KarpGeneralError):
                if error.user_msg:
                    return str(error.user_msg), 400
                else:
                    return error.message, 400

            else:
                response = jsonify(error.to_dict())
                response.status_code = error.status_code
                return response
        else:
            logging.exception(error.message)
            return "Oops, something went wrong\n", 500

    except Exception:
        # In case of write conflicts etc, print to anoter file
        # and send email to admin
        import time
        import traceback
        logdir = configM.config['DEBUG']['LOGDIR']
        dbconf = configM.config['DB']
        trace = traceback.format_exc()
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        msg = 'Cannot print log file: %s, %s' % (date, trace)
        title = 'Karp urgent logging error'
        if dbconf['admin_emails']:
            import dbhandler.emailsender as email
            email.send_notification(dbconf['admin_emails'], title, msg)
        open(logdir+'KARPERR'+time.strftime("%Y%m%d"), 'a').write(msg)
        return "Oops, something went wrong\n", 500
