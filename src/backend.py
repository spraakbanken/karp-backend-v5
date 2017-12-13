# -*- coding: utf-8 -*-

from flask import jsonify, request, session
from src.server.helper.utils import route
import src.server.checkdbhistory as checkdbhistory
import src.server.searching as searching
import src.server.suggestions as suggestions
import src.server.update as update
import src.server.helper.configmanager as configM


""" The backend, redirects url calls to the appropriate modules.
    Is also responsible for which ES node to query.
"""


def init():
    urls = []

    @route(urls)
    def autoupdate():
        import server.autoupdates as a
        import logging
        import datetime
        """ Asking a query and requesting a specific page of the answer """
        logging.debug('\n\nhello')
        print('\n\nhello')
        doc = {}
        date = datetime.datetime.now()
        doc2 = a.auto_update_document(doc, 'saol', 'update', 'testuser', date)
        return doc2

    @route(urls)
    def explain():
        """ Asking a query and requesting a specific page of the answer """
        return searching.explain()


    @route(urls)
    def query(page=0):
        """ Querying the database """
        return searching.query(page=page)


    @route(urls)
    def querycount(page=0):
        """ Querying the database """
        return searching.querycount(page=page)


    @route(urls)
    def minientry():
        """ Returns just some information about the results """
        return searching.minientry()


    @route(urls)
    def statistics():
        """ Returns the counts and statistics """
        return searching.statistics()


    @route(urls)
    def statlist():
        """ Returns the counts and statistics """
        return searching.statlist()


    @route(urls)
    def random():
        return searching.random()


    @route(urls)
    def autocomplete():
        return searching.autocomplete()


    # For seeing the posted data formated
    @route(urls, 'format')
    def format():
        return searching.formatpost()


    # For seeing the posted data formated
    @route(urls, '<lexicon>')
    def export(lexicon):
        return searching.export(lexicon)


    # For deleting a lexical entry from elastic and sql
    @route(urls, '<lexicon>/<_id>')
    def delete(lexicon, _id):
        return update.delete_entry(lexicon, _id, sql=True)


    # For updating a document
    @route(urls, '<lexicon>/<_id>', methods=['POST'])
    def mkupdate(lexicon, _id):
        return update.update_doc(lexicon, _id)


    # For adding a document
    @route(urls, '<lexicon>', methods=['POST'])
    def add(lexicon):
        return update.add_doc(lexicon)


    # For adding a document which already has an id (one that has been deleted)
    @route(urls, '<lexicon>/<_id>', methods=['POST'])
    def readd(lexicon, _id):
            return update.add_doc(lexicon, _id=_id)


    # For adding many document
    @route(urls, '<lexicon>', methods=['POST'])
    def addbulk(lexicon):
        return update.add_multi_doc(lexicon)


    @route(urls, '<lexicon>/<parentid>', methods=['POST'])
    def addchild(lexicon, parentid):
        return update.add_child(lexicon, parentid, suggestion=False)


    # For checking which resources a user may edit
    @route(urls, methods=['GET'])
    def checkuser():
        return update.checkuser()


    # For retrieving update history of an entry
    @route(urls, '<lexicon>/<_id>')
    def checkhistory(lexicon, _id):
        return checkdbhistory.checkhistory(lexicon, _id)


    # For retrieving update history of a user
    @route(urls)
    def checkuserhistory():
        return checkdbhistory.checkuserhistory()


    # For retrieving update history of one lexicon
    @route(urls, '<lexicon>')
    @route(urls, '<lexicon>/<date>')
    def checklexiconhistory(lexicon, date=''):
        try:
            return checkdbhistory.checklexiconhistory(lexicon, date=date)
        except Exception as e:
            raise e


    # For retrieving the lexicon order of a lexicon
    @route(urls)
    def lexiconorder():
        return searching.lexiconorder()


    # For retrieving the difference between two versions
    @route(urls, '<lexicon>/<_id>/latest')
    @route(urls, '<lexicon>/<_id>/latest/<fromdate>')
    @route(urls, '<lexicon>/<_id>/<fromdate>/<todate>')
    def checkdifference(_id, lexicon, todate='', fromdate=''):
        return checkdbhistory.comparejson(lexicon, _id, todate=todate,
                                          fromdate=fromdate)


    # For submitting a suggestion
    @route(urls, name='/suggestnew/<lexicon>', methods=['POST'])
    @route(urls, '<lexicon>/<_id>', methods=['POST'])
    def suggest(lexicon, _id=None):
        return suggestions.suggest(lexicon, _id)


    # For seeing suggestions
    @route(urls)
    def checksuggestions():
        return suggestions.checksuggestions()


    # For accepting a suggestion
    @route(urls, '<lexicon>/<_id>', methods=['POST'])
    def acceptsuggestion(lexicon, _id):
        return suggestions.acceptsuggestion(lexicon, _id)


    # For accepting a suggestion
    @route(urls, '<lexicon>/<_id>', methods=['POST'])
    def acceptandmodified(lexicon, _id):
        return suggestions.acceptmodified(lexicon, _id)


    # For rejecting a suggestion
    @route(urls, '<lexicon>/<_id>', methods=['POST'])
    def rejectsuggestion(lexicon, _id):
        return suggestions.rejectsuggestion(lexicon, _id)


    # For seeing the status of a suggestion
    @route(urls, '<lexicon>/<_id>')
    def checksuggestion(lexicon, _id):
        return suggestions.checksuggestion(lexicon, _id)


    # For seeing entries that are the alphabetically close
    @route(urls, '<lexicon>')
    def getcontext(lexicon):
        return searching.get_context(lexicon)


    @route(urls, '<mode>')
    def modeinfo(mode):
        """ Asking a query and requesting a specific page of the answer """
        return searching.modeinfo(mode)


    @route(urls, '<lexicon>')
    def lexiconinfo(lexicon):
        """ Asking a query and requesting a specific page of the answer """
        return searching.lexiconinfo(lexicon)


    @route(urls)
    def modes():
        jsonmodes = {}
        for mode, info in configM.searchconfig.items():
            jsonmodes[mode] = info.get('groups', {})
        return jsonify(jsonmodes)


    @route(urls)
    def groups():
        modes = {}
        for name, val in configM.lexiconconfig.items():
            if val[0] in modes:
                modes[val[0]].append('%s (%s)' % (name, val[1]))
            else:
                modes[val[0]] = ['%s (%s)' % (name, val[1])]
        olist = ''
        for mode, kids in modes.items():
            olist += ('<li>%s<ul>%s</ul></li>'
                      % (mode, '\n'.join('<li>%s</li>' % kid for kid in kids)))
        return '<ul> %s </ul>' % olist



    # ------------------- HTML FILES ------------------- #

    # Other ways of finding and sending files:
    # http://flask.pocoo.org/docs/0.10/api/#flask.Flask.open_resource
    # http://flask.pocoo.org/docs/0.10/api/#flask.Flask.send_static_file
    @route(urls)
    def order():
        orderlist = []
        for name, val in configM.lexiconconfig.conf.items():
            orderlist.append((val[1], '%s (%s)' % (name, val[0])))
        olist = '\n'.join('<li>%d: %s</li>' % on for on in sorted(orderlist))
        return '<ul> %s </ul>' % olist


    @route(urls, name='/')
    @route(urls, name='/index')
    def helppage():
        import os
        import re
        import logging
        project_dir = os.path.join(os.path.dirname(__file__))
        logging.debug('path %s' % project_dir)
        html_dir = os.path.join(configM.setupconfig['script_path'], 'html')
        doc_file = 'index_dokumentation.html'
        with app.open_resource(os.path.join(html_dir, doc_file)) as f:
            contents = f.read()
        contents = re.sub('URL/', request.url.encode('utf8'), contents)
        return contents


    @route(urls, '/logout')
    def logout():
        # remove the username from the session if it's there
        session.pop('username', None)
        session.pop('lexicon_list', None)
        return jsonify({"logged_out": True})

    return urls
