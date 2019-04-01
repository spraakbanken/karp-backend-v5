# -*- coding: utf-8 -*-
""" The backend, redirects url calls to the appropriate modules.
    Is also responsible for which ES node to query.
"""

from flask import jsonify, request, session
#from karp5.server.helper.flaskhelper import app
#import karp5.server.checkdbhistory as checkdbhistory
#import karp5.server.idgenerator as idgenerator
#import karp5.server.searching as searching
#import karp5.server.suggestions as suggestions
#import karp5.server.update as update
#import karp5.server.helper.configmanager as configM
#import karp5
import logging
from app.search import bp


@bp.route()
def explain():
    """ Asking a query and show the elastic query """
    return searching.explain()

@bp.route()
def test():
    """ Show the elastic query """
    return searching.test()

@bp.route()
def query(page=0):
    """ Querying the database """
    return searching.query(page=page)

@bp.route()
def querycount(page=0):
    """ Querying the database """
    return searching.querycount(page=page)

@bp.route()
def minientry():
    """ Returns just some information about the results """
    return searching.minientry()

@bp.route()
def statistics():
    """ Returns the counts and statistics """
    return searching.statistics()

@bp.route()
def statlist():
    """ Returns the counts and statistics """
    return searching.statlist()

@bp.route()
def random():
    return searching.random()

@bp.route()
def autocomplete():
    return searching.autocomplete()

# For seeing the posted data formated
@bp.route()
def format():
    return searching.formatpost()

# For getting a possible new identifier for an entry
@bp.route('<mode>')
def suggestid(mode):
    return jsonify({"suggested_id": idgenerator.suggest_id(mode)})

# For seeing the posted data formated
@bp.route('<lexicon>')
def export(lexicon):
    return searching.export(lexicon)


# TODO remove For seeing the posted data formated
@bp.route('<lexicon>/<divsize>')
def export2(lexicon, divsize=5000):
    return searching.export2(lexicon, divsize)

    # For deleting a lexical entry from elastic and sql
    @bp.route('<lexicon>/<_id>')
    def delete(lexicon, _id):
        return update.delete_entry(lexicon, _id, sql=True)

    # For updating a document
    @bp.route('<lexicon>/<_id>', methods=['POST'])
    def mkupdate(lexicon, _id):
        return update.update_doc(lexicon, _id)

    # For adding a document
    @bp.route('<lexicon>', methods=['POST'])
    def add(lexicon):
        return update.add_doc(lexicon)

    # For adding a document which already has an id (one that has been deleted)
    @bp.route('<lexicon>/<_id>', methods=['POST'])
    def readd(lexicon, _id):
        return update.add_doc(lexicon, _id=_id)

    # For adding many document
    @bp.route('<lexicon>', methods=['POST'])
    def addbulk(lexicon):
        return update.add_multi_doc(lexicon)

    @bp.route('<lexicon>/<parentid>', methods=['POST'])
    def addchild(lexicon, parentid):
        return update.add_child(lexicon, parentid, suggestion=False)

    # For checking which resources a user may edit
    @bp.route(methods=['GET'])
    def checkuser():
        return update.checkuser()

    # For retrieving update history of an entry
    @bp.route('<lexicon>/<_id>')
    def checkhistory(lexicon, _id):
        return checkdbhistory.checkhistory(lexicon, _id)

    # For retrieving update history of a user
    @bp.route()
    def checkuserhistory():
        return checkdbhistory.checkuserhistory()

    # For retrieving update history of one lexicon
    @bp.route('<lexicon>')
    @bp.route('<lexicon>/<date>')
    def checklexiconhistory(lexicon, date=''):
        try:
            return checkdbhistory.checklexiconhistory(lexicon, date=date)
        except Exception as e:
            raise e

    # For retrieving the lexicon order of a lexicon
    @bp.route()
    def lexiconorder():
        return searching.lexiconorder()

    # For retrieving the difference between two versions
    @bp.route('<lexicon>/<_id>/latest')
    @bp.route('<lexicon>/<_id>/latest/<fromdate>')
    @bp.route('<lexicon>/<_id>/<fromdate>/<todate>')
    def checkdifference(_id, lexicon, todate='', fromdate=''):
        return checkdbhistory.comparejson(lexicon, _id, todate=todate,
                                          fromdate=fromdate)

    # For submitting a suggestion
    @bp.route(name='/suggestnew/<lexicon>', methods=['POST'])
    @bp.route('<lexicon>/<_id>', methods=['POST'])
    def suggest(lexicon, _id=None):
        return suggestions.suggest(lexicon, _id)

    # For seeing suggestions
    @bp.route()
    def checksuggestions():
        return suggestions.checksuggestions()

    # For accepting a suggestion
    @bp.route('<lexicon>/<_id>', methods=['POST'])
    def acceptsuggestion(lexicon, _id):
        return suggestions.acceptsuggestion(lexicon, _id)

    # For accepting a suggestion
    @bp.route('<lexicon>/<_id>', methods=['POST'])
    def acceptandmodify(lexicon, _id):
        return suggestions.acceptmodified(lexicon, _id)

    # For rejecting a suggestion
    @bp.route('<lexicon>/<_id>', methods=['POST'])
    def rejectsuggestion(lexicon, _id):
        return suggestions.rejectsuggestion(lexicon, _id)

    # For seeing the status of a suggestion
    @bp.route('<lexicon>/<_id>')
    def checksuggestion(lexicon, _id):
        return suggestions.checksuggestion(lexicon, _id)

    # For seeing entries that are the alphabetically close
    @bp.route('<lexicon>')
    def getcontext(lexicon):
        return searching.get_context(lexicon)

    @bp.route('<mode>')
    def modeinfo(mode):
        """ Show information about a mode """
        return searching.modeinfo(mode)

    @bp.route('<lexicon>')
    def lexiconinfo(lexicon):
        """ Show information about a lexicon """
        return searching.lexiconinfo(lexicon)

    @bp.route()
    def modes():
        jsonmodes = {}
        for mode, info in configM.searchconfig.items():
            jsonmodes[mode] = info.get('groups', {})
        return jsonify(jsonmodes)

    @bp.route()
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
    @bp.route()
    def order():
        orderlist = []
        for name, val in configM.lexiconconfig.conf.items():
            orderlist.append((val['order'], '%s (%s)' % (name, val[0])))
        olist = '\n'.join('<li>%d: %s</li>' % on for on in sorted(orderlist))
        return '<ul> %s </ul>' % olist

    @bp.route(name='/')
    @bp.route(name='/index')
    def helppage():
        """Render API documentation."""
        logging.debug('ok')
        import os
        import markdown

        logging.debug('index page')

        KARP_API_URL = configM.setupconfig.get('BACKEND_URL', 'https://ws.spraakbanken.gu.se/ws/karp/v5')
        KARP_VERSION = "5"
        STYLES_CSS = 'static/api.css'
        logging.debug("abs path: %s", configM.setupconfig['ABSOLUTE_PATH'])

        # doc_dir = os.path.join(configM.setupconfig['ABSOLUTE_PATH'], 'src', 'html')
        # doc_file = 'api.md'
        #
        # with app.open_resource(os.path.join(doc_dir, doc_file)) as doc:
        #     md_text = doc.read()
        #     logging.debug("md_text: %s", type(md_text))
        #     md_text = md_text.decode("UTF-8")
        #     logging.debug("md_text: %s", type(md_text))

        md_text = karp5.get_pkg_resource('html/api.md')
        logging.debug("md_text: %s", type(md_text))
        # Replace placeholders
        md_text = md_text.replace("[SBURL]", KARP_API_URL)
        md_text = md_text.replace('[SBVERSION]', karp5.get_version())
        # md_text = md_text.replace("[URL]", request.base_url)
        # md_text = md_text.replace("[VERSION]", KARP_VERSION)

        # Convert Markdown to HTML
        md = markdown.Markdown(extensions=["markdown.extensions.toc",
                                           "markdown.extensions.smarty",
                                           "markdown.extensions.def_list",
                                           "markdown.extensions.tables"])
        md_html = md.convert(md_text)
        md_html = md_html.replace("<pre><code>", '<pre><code class="json">')

        html = ["""<!doctype html>
            <html>
              <head>
                <meta charset="utf-8">
                <title>Karp API v%s</title>
                <link href="//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/styles/monokai-sublime.min.css"
                  rel="stylesheet">
                <script src="//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/highlight.min.js"></script>
                <script>hljs.initHighlightingOnLoad();</script>
                <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
                <link href="https://fonts.googleapis.com/css?family=Roboto+Slab" rel="stylesheet">
                <link href="%s" rel="stylesheet">
              </head>
              <body>
                <div class="toc-wrapper">
                  <div class="header">
                    <img src="static/karp.png"><br><br>
                    Karp API <span>v%s</span>
                  </div>
                  %s
                </div>
               <div class="content">
                """ % (KARP_VERSION, STYLES_CSS, KARP_VERSION, md.toc), md_html, "</div></body></html>"]

        return "\n".join(html)

    @bp.route('/logout')
    def logout():
        # remove the username from the session if it's there
        session.pop('username', None)
        session.pop('lexicon_list', None)
        return jsonify({"logged_out": True})
