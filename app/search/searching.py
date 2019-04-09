# -*- coding: utf-8 -*-
""" The backend, redirects url calls to the appropriate modules.
    Is also responsible for which ES node to query.
"""
from __future__ import unicode_literals

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


def explain():
    """ Asking a query and show the elastic query """
    return 'searching.explain()'


def test():
    """ Show the elastic query """
    return 'searching.test()'


def query(page=0):
    """ Querying the database """
    return f'searching.query(page={page})'


def querycount(page=0):
    """ Querying the database """
    return f'searching.querycount(page={page})'
    

def minientry():
    """ Returns just some information about the results """
    return 'searching.minientry()'
    

def statistics():
    """ Returns the counts and statistics """
    return 'searching.statistics()'
    

def statlist():
    """ Returns the counts and statistics """
    return 'searching.statlist()'


def random():
    return 'searching.random()'


def autocomplete():
    return 'searching.autocomplete()'
    

# For seeing the posted data formated
def format():
    return 'searching.formatpost()'
    

# TODO remove For seeing the posted data formated
def export2(lexicon, divsize=5000):
    return f'searching.export2({lexicon}, {divsize})'
    

# For retrieving the lexicon order of a lexicon
def lexiconorder():
    return f'searching.lexiconorder()'
    

# For seeing entries that are the alphabetically close
def getcontext(lexicon):
    return f'searching.get_context(lexicon={lexicon})'
    

def modeinfo(mode):
    """ Show information about a mode """
    return f'searching.modeinfo(mode{mode})'


def lexiconinfo(lexicon):
    """ Show information about a lexicon """
    return f'searching.lexiconinfo({lexicon})'
