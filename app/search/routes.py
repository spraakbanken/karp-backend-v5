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
#from karp5.config import mgr as conf_mgr
#import karp5
import logging

from app.search import searching
from app.search import bp


@bp.route('/explain')
def explain():
    """ Asking a query and show the elastic query """
    return searching.explain()

@bp.route('/test')
def test():
    """ Show the elastic query """
    return searching.test()



@bp.route('/query')
@bp.route('/query/<page>')
def query(page=0):
    """ Querying the database """
    return searching.query(page=page)


@bp.route('/querycount')
@bp.route('/querycount/<page>')
def querycount(page=0):
    """ Querying the database """
    return searching.querycount(page=page)


@bp.route('/minientry')
def minientry():
    """ Returns just some information about the results """
    return searching.minientry()


@bp.route('/statistics')
def statistics():
    """ Returns the counts and statistics """
    return searching.statistics()


@bp.route('/statlist')
def statlist():
    """ Returns the counts and statistics """
    return searching.statlist()


@bp.route('/random')
def random():
    return searching.random()


@bp.route('/autocomplete')
def autocomplete():
    return searching.autocomplete()


# For seeing the posted data formated
@bp.route('/format')
def format():
    return searching.formatpost()


# TODO remove For seeing the posted data formated
@bp.route('/export2/<lexicon>')
@bp.route('/export2/<lexicon>/<divsize>')
def export2(lexicon, divsize=5000):
    return searching.export2(lexicon, divsize)


# For retrieving the lexicon order of a lexicon
@bp.route('/lexiconorder')
def lexiconorder():
    return searching.lexiconorder()


# For seeing entries that are the alphabetically close
@bp.route('/getcontext/<lexicon>')
def getcontext(lexicon):
    return searching.get_context(lexicon)


@bp.route('/modeinfo/<mode>')
def modeinfo(mode):
    """ Show information about a mode """
    return searching.modeinfo(mode)


@bp.route('/lexiconinfo/<lexicon>')
def lexiconinfo(lexicon):
    """ Show information about a lexicon """
    return searching.lexiconinfo(lexicon)
