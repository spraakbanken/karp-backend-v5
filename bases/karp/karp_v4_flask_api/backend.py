# import this to start up the logging
from karp.server import log

from elasticsearch import ConnectionError
from flask import jsonify, request, session
from config import setup as setupconf
from karp.server.helper import config_manager as configM
from .flaskhelper import app, crossdomain
from karp.server import checkdbhistory
from karp.server import errorhandler as eh
from karp.server import searching 
from karp.server import suggestions 
from karp.server import update 


# Special imports for special modes
# import and make the route to saldopath
from karp.sb.backend import saldopath
from karp.skbl.skblbackend import getplaces


""" The backend, redirects url calls to the appropriate modules.
    Is also responsible for which ES node to query.
"""


@app.route('/explain')
@crossdomain(origin='*')
def explain():
    """ Asking a query and requesting a specific page of the answer """
    return searching.explain(elastic)


@app.route('/query')
@crossdomain(origin='*')
def query(page=0):
    """ Querying the database """
    return searching.query(elastic, page=page)


@app.route('/querycount')
@crossdomain(origin='*')
def querycount(page=0):
    """ Querying the database """
    return searching.querycount(elastic, page=page)


@app.route('/minientry')
@crossdomain(origin='*')
def minientry():
    """ Returns just some information about the results """
    return searching.minientry(elastic)


@app.route('/statistics')
@crossdomain(origin='*')
def statistics():
    """ Returns the counts and statistics """
    return searching.statistics(elastic)


@app.route('/statlist')
@crossdomain(origin='*')
def statlist():
    """ Returns the counts and statistics """
    return searching.statlist(elastic)


@app.route('/random')
@crossdomain(origin='*')
def random():
    return searching.random(elastic)


@app.route('/autocomplete')
@crossdomain(origin='*')
def autocomplete():
    return searching.autocomplete(elastic)


# For seeing the posted data formated
@app.route('/format', methods=['POST'])
@crossdomain(origin='*')
def formatpost():
    return searching.formatpost(elastic)


# For seeing the posted data formated
@app.route('/export/<lexicon>')
@crossdomain(origin='*')
def export(lexicon):
    return searching.export(lexicon)


# For deleting a lexical entry from elastic and sql
@app.route('/delete/<lexicon>/<_id>')
@crossdomain(origin='*')
def delete_entry(lexicon, _id):
    return update.delete_entry(lexicon, _id, elastic, sql=True)


# For updating a document
@app.route('/mkupdate/<lexicon>/<_id>', methods=['POST'])
@crossdomain(origin='*')
def mkupdate(lexicon, _id):
    return update.update_doc(lexicon, _id, elastic)


# For adding a document
@app.route('/add/<lexicon>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def adddoc(lexicon):
    return update.add_doc(lexicon, elastic)


# For adding a document which already has an id (one that has been deleted)
@app.route('/readd/<lexicon>/<_id>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def readddoc(lexicon, _id):
        return update.add_doc(lexicon, elastic, _id=_id)


# For adding many document
@app.route('/addbulk/<lexicon>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def addbulk(lexicon):
    return update.add_multi_doc(lexicon, elastic)


@app.route('/addchild/<lexicon>/<parentid>', methods=['POST'])
def add_child(lexicon, parentid):
    return update.add_child(lexicon, elastic, parentid, suggestion=False)


# For checking which resources a user may edit
@app.route('/checkuser', methods=['GET'])
@crossdomain(origin='*')
def checkuser():
    return update.checkuser()


# For retrieving update history of an entry
@app.route('/checkhistory/<lexicon>/<_id>')
@crossdomain(origin='*')
def checkhistory(lexicon, _id):
    return checkdbhistory.checkhistory(lexicon, _id)


# For retrieving update history of a user
@app.route('/checkuserhistory')
@crossdomain(origin='*')
def checkuserhistory():
    return checkdbhistory.checkuserhistory()


# For retrieving update history of one lexicon
@app.route('/checklexiconhistory/<lexicon>')
@app.route('/checklexiconhistory/<lexicon>/<date>')
@crossdomain(origin='*')
def checklexiconhistory(lexicon, date=''):
    try:
        return checkdbhistory.checklexiconhistory(lexicon, date=date)
    except Exception as e:
        raise e


# For retrieving the lexicon order
@app.route('/lexiconorder')
@crossdomain(origin='*')
def lexiconorder():
    return searching.lexiconorder()


# For retrieving the difference between two versions
@app.route('/checkdifference/<lexicon>/<_id>/latest')
@app.route('/checkdifference/<lexicon>/<_id>/latest/<fromdate>')
@app.route('/checkdifference/<lexicon>/<_id>/<fromdate>/<todate>')
@crossdomain(origin='*')
def checkdifference(_id, lexicon, todate='', fromdate=''):
    return checkdbhistory.comparejson(lexicon, _id, todate=todate,
                                      fromdate=fromdate)


# For submitting a suggestion
@app.route('/suggestnew/<lexicon>', methods=['POST'])
@app.route('/suggest/<lexicon>/<_id>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def suggest(lexicon, _id=None):
    return suggestions.suggest(lexicon, _id, elastic)


# For seeing suggestions
@app.route('/checksuggestions')
@crossdomain(origin='*')
def checksuggestions():
    return suggestions.checksuggestions()


# For accepting a suggestion
@app.route('/acceptsuggestion/<lexicon>/<_id>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def acceptsuggest(lexicon, _id):
    return suggestions.acceptsuggestion(lexicon, _id, elastic)


# For accepting a suggestion
@app.route('/acceptandmodify/<lexicon>/<_id>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def acceptmodified(lexicon, _id):
    return suggestions.acceptmodified(lexicon, _id, elastic)


# For rejecting a suggestion
@app.route('/rejectsuggestion/<lexicon>/<_id>', methods=['POST'])
@crossdomain(origin='*', methods=['POST'])
def rejectsuggest(lexicon, _id):
    return suggestions.rejectsuggestion(lexicon, _id, elastic)


# For seeing the status of a suggestion
@app.route('/checksuggestion/<lexicon>/<_id>')
@crossdomain(origin='*')
def checksuggest(lexicon, _id):
    return suggestions.checksuggestion(lexicon, _id)


# For seeing entries that are the alphabetically close
@app.route('/getcontext/<lexicon>')
@crossdomain(origin='*')
def get_context(lexicon):
    return searching.get_context(lexicon, elastic)


# Constructs a Elasticsearch-py objects with addresses to all nodes
def elastic(mode='', lexicon=''):
    return configM.elastic(mode=mode, lexicon=lexicon)


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
            % (request.full_path, user, e_type, str(error), data)
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

    except Exception as e:
        # In case of write conflicts etc, print to anoter file
        # and send email to admin
        import time
        from config import dbconf
        from config import debugmode
        import traceback
        trace = traceback.format_exc()
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        msg = 'Cannot print log file: %s, %s' % (date, trace)
        title = 'Karp urgent logging error'
        if dbconf.admin_emails:
            from karp.dbhandler import emailsender as email
            email.send_notification(dbconf.admin_emails, title, msg)
        open(debugmode.LOGDIR+'KARPERR'+time.strftime("%Y%m%d"), 'a').write(msg)
        return "Oops, something went wrong\n", 500


# For debugging
# replaced by validatequery
# @app.route('/testquery', methods=['GET'])
# @crossdomain(origin='*')
# def testquery():
#     return searching.testquery()
#

@app.route('/modeinfo/<mode>')
@crossdomain(origin='*')
def modeinfo(mode):
    """ Asking a query and requesting a specific page of the answer """
    return searching.modeinfo(mode)


@app.route('/lexiconinfo/<lexicon>')
@crossdomain(origin='*')
def lexiconinfo(lexicon):
    """ Asking a query and requesting a specific page of the answer """
    return searching.lexiconinfo(lexicon)


@app.route('/modes')
def showmodes():
    from .config import modes
    jsonmodes = {}
    for mode, info in list(modes.modes.items()):
        jsonmodes[mode] = info.get('groups', {})
    return jsonify(jsonmodes)


@app.route('/groups')
def showgroups():
    from .config import lexiconconf
    modes = {}
    for name, val in list(lexiconconf.conf.items()):
        if val[0] in modes:
            modes[val[0]].append('%s (%s)' % (name, val[1]))
        else:
            modes[val[0]] = ['%s (%s)' % (name, val[1])]
    olist = ''
    for mode, kids in list(modes.items()):
        olist += ('<li>%s<ul>%s</ul></li>'
                  % (mode, '\n'.join('<li>%s</li>' % kid for kid in kids)))
    return '<ul> %s </ul>' % olist


# ------------------- HTML FILES ------------------- #

# Other ways of finding and sending files:
# http://flask.pocoo.org/docs/0.10/api/#flask.Flask.open_resource
# http://flask.pocoo.org/docs/0.10/api/#flask.Flask.send_static_file
@app.route('/order')
def showorder():
    from .config import lexiconconf
    orderlist = []
    for name, val in list(lexiconconf.conf.items()):
        orderlist.append((val[1], '%s (%s)' % (name, val[0])))
    olist = '\n'.join('<li>%d: %s</li>' % on for on in sorted(orderlist))
    return '<ul> %s </ul>' % olist


@app.route('/')
@app.route('/index')
def helppage():
    import os
    import re
    html_dir = 'html'
    doc_file = 'index_dokumentation.html'
    with app.open_resource(os.path.join(html_dir, doc_file)) as f:
        contents = f.read()
    contents = re.sub('URL/', request.url, contents.decode('utf-8'))
    return contents


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('lexicon_list', None)
    return jsonify({"logged_out": True})


# set the secret key
app.secret_key = setupconf.secret_key

if __name__ == '__main__':
    app.run()
