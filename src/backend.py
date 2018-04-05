# -*- coding: utf-8 -*-

from flask import jsonify, request, session
from src.server.helper.flaskhelper import app
import src.server.checkdbhistory as checkdbhistory
import src.server.searching as searching
import src.server.suggestions as suggestions
import src.server.update as update
import src.server.helper.configmanager as configM
import logging


""" The backend, redirects url calls to the appropriate modules.
    Is also responsible for which ES node to query.
"""


def init(route):

    @route()
    def explain():
        """ Asking a query and show the elastic query """
        return searching.explain()

    @route()
    def test():
        """ Show the elastic query """
        return searching.test()

    @route()
    def query(page=0):
        """ Querying the database """
        return searching.query(page=page)

    @route()
    def querycount(page=0):
        """ Querying the database """
        return searching.querycount(page=page)

    @route()
    def minientry():
        """ Returns just some information about the results """
        return searching.minientry()

    @route()
    def statistics():
        """ Returns the counts and statistics """
        return searching.statistics()

    @route()
    def statlist():
        """ Returns the counts and statistics """
        return searching.statlist()

    @route()
    def random():
        return searching.random()

    @route()
    def autocomplete():
        return searching.autocomplete()

    # For seeing the posted data formated
    @route('format')
    def format():
        return searching.formatpost()

    # For seeing the posted data formated
    @route('<lexicon>')
    def export(lexicon):
        return searching.export(lexicon)

    # For deleting a lexical entry from elastic and sql
    @route('<lexicon>/<_id>')
    def delete(lexicon, _id):
        return update.delete_entry(lexicon, _id)

    # For updating a document
    @route('<lexicon>/<_id>', methods=['POST'])
    def mkupdate(lexicon, _id):
        return update.update_doc(lexicon, _id)

    # For adding a document
    @route('<lexicon>', methods=['POST'])
    def add(lexicon):
        return update.add_doc(lexicon)

    # For adding a document which already has an id (one that has been deleted)
    @route('<lexicon>/<_id>', methods=['POST'])
    def readd(lexicon, _id):
            return update.add_doc(lexicon, _id=_id)

    # For adding many document
    @route('<lexicon>', methods=['POST'])
    def addbulk(lexicon):
        return update.add_multi_doc(lexicon)

    @route('<lexicon>/<parentid>', methods=['POST'])
    def addchild(lexicon, parentid):
        return update.add_child(lexicon, parentid, suggestion=False)

    # For checking which resources a user may edit
    @route(methods=['GET'])
    def checkuser():
        return update.checkuser()

    # For retrieving update history of an entry
    @route('<lexicon>/<_id>')
    def checkhistory(lexicon, _id):
        return checkdbhistory.checkhistory(lexicon, _id)

    # For retrieving update history of a user
    @route()
    def checkuserhistory():
        return checkdbhistory.checkuserhistory()

    # For retrieving update history of one lexicon
    @route('<lexicon>')
    @route('<lexicon>/<date>')
    def checklexiconhistory(lexicon, date=''):
        try:
            return checkdbhistory.checklexiconhistory(lexicon, date=date)
        except Exception as e:
            raise e

    # For retrieving the lexicon order of a lexicon
    @route()
    def lexiconorder():
        return searching.lexiconorder()

    # For retrieving the difference between two versions
    @route('<lexicon>/<_id>/latest')
    @route('<lexicon>/<_id>/latest/<fromdate>')
    @route('<lexicon>/<_id>/<fromdate>/<todate>')
    def checkdifference(_id, lexicon, todate='', fromdate=''):
        return checkdbhistory.comparejson(lexicon, _id, todate=todate,
                                          fromdate=fromdate)

    # For submitting a suggestion
    @route(name='/suggestnew/<lexicon>', methods=['POST'])
    @route('<lexicon>/<_id>', methods=['POST'])
    def suggest(lexicon, _id=None):
        return suggestions.suggest(lexicon, _id)

    # For seeing suggestions
    @route()
    def checksuggestions():
        return suggestions.checksuggestions()

    # For accepting a suggestion
    @route('<lexicon>/<_id>', methods=['POST'])
    def acceptsuggestion(lexicon, _id):
        return suggestions.acceptsuggestion(lexicon, _id)

    # For accepting a suggestion
    @route('<lexicon>/<_id>', methods=['POST'])
    def acceptandmodify(lexicon, _id):
        return suggestions.acceptmodified(lexicon, _id)

    # For rejecting a suggestion
    @route('<lexicon>/<_id>', methods=['POST'])
    def rejectsuggestion(lexicon, _id):
        return suggestions.rejectsuggestion(lexicon, _id)

    # For seeing the status of a suggestion
    @route('<lexicon>/<_id>')
    def checksuggestion(lexicon, _id):
        return suggestions.checksuggestion(lexicon, _id)

    # For seeing entries that are the alphabetically close
    @route('<lexicon>')
    def getcontext(lexicon):
        return searching.get_context(lexicon)

    @route('<mode>')
    def modeinfo(mode):
        """ Show information about a mode """
        return searching.modeinfo(mode)

    @route('<lexicon>')
    def lexiconinfo(lexicon):
        """ Show information about a lexicon """
        return searching.lexiconinfo(lexicon)

    @route()
    def modes():
        jsonmodes = {}
        for mode, info in configM.searchconfig.items():
            jsonmodes[mode] = info.get('groups', {})
        return jsonify(jsonmodes)

    @route()
    def groups():
        modes = {}
        for name, val in configM.lexiconconfig.items():
            if name == "default":
                continue
            if val['mode'] in modes:
                modes[val['mode']].append('%s (%s)' % (name, val['order']))
            else:
                modes[val['mode']] = ['%s (%s)' % (name, val['order'])]
        olist = ''
        for mode, kids in modes.items():
            olist += ('<li>%s<ul>%s</ul></li>'
                      % (mode, '\n'.join('<li>%s</li>' % kid for kid in kids)))
        return '<ul> %s </ul>' % olist

    # ------------------- HTML FILES ------------------- #
    # Other ways of finding and sending files:
    # http://flask.pocoo.org/docs/0.10/api/#flask.Flask.open_resource
    # http://flask.pocoo.org/docs/0.10/api/#flask.Flask.send_static_file
    @route()
    def order():
        orderlist = []
        for name, val in configM.lexiconconfig.conf.items():
            orderlist.append((val['order'], '%s (%s)' % (name, val[0])))
        olist = '\n'.join('<li>%d: %s</li>' % on for on in sorted(orderlist))
        return '<ul> %s </ul>' % olist

    @route(name='/')
    @route(name='/index')
    def helppage():
        logging.debug('index page')
        logging.debug('\n\n')
        import os
        import re
        project_dir = os.path.join(os.path.dirname(__file__))
        logging.debug('path %s' % project_dir)
        # html_dir = os.path.join('src', 'html')
        html_dir = os.path.join(configM.setupconfig['ABSOLUTE_PATH'],  'html')
        doc_file = 'index_dokumentation.html'
        logging.debug('open %s' % os.path.join(html_dir, doc_file))
        with app.open_resource(os.path.join(html_dir, doc_file)) as f:
            contents = f.read()
        contents = re.sub('URL/', request.url.encode('utf8'), contents)
        return contents

    @route('/logout')
    def logout():
        # remove the username from the session if it's there
        session.pop('username', None)
        session.pop('lexicon_list', None)
        return jsonify({"logged_out": True})
