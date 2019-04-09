from __future__ import unicode_literals
from builtins import object
import json
import logging
import os

from elasticsearch import Elasticsearch

import six

import karp5.server.helper.configpaths as C
import karp5.server.errorhandler as eh
from karp5.server.translator import fieldmapping as F
from karp5.instance_info import get_instance_path


_logger = logging.getLogger('karp5')


def set_defaults(data):
    defaults = data.get('default', None)
    if not defaults:
        return
    for data_key, data_val in six.viewitems(data):
        if data_key != 'default':
            for def_key, def_val in six.viewitems(defaults):
                if def_key not in data_val:
                    data_val[def_key] = def_val


configdir = os.path.join(get_instance_path(), 'config')




class ConfigManager(object):
    def __init__(self):
        self.searchconfig = {}
        self.config = {}
        self.lexiconconfig = {}
        self.defaultfields = {}
        self.app_config = None
        self.load_config()

    def load_config(self):
        with open(os.path.join(configdir, 'modes.json')) as fp:
            self.searchconfig = json.load(fp)
        set_defaults(self.searchconfig)

        with open(os.path.join(configdir, 'lexiconconf.json')) as fp:
	        self.lexiconconfig = json.load(fp)
        set_defaults(self.lexiconconfig)

        with open(os.path.join(configdir, 'config.json')) as fp:
	        self.config = json.load(fp)

        with open(os.path.join(configdir, 'mappings/fieldmappings_default.json')) as fp:
	        self.defaultfields = json.load(fp)

    def override_elastic_url(self, elastic_url):
        for mode, mode_settings in six.viewitems(self.searchconfig):
            mode_settings['elastic_url'] = elastic_url



_configmanager = ConfigManager()

searchconfig = _configmanager.searchconfig
config = _configmanager.config
lexiconconfig = _configmanager.lexiconconfig
setupconfig = config['SETUP']
standardmode = setupconfig['STANDARDMODE']

def override_elastic_url(elastic_url):
    _configmanager.override_elastic_url(elastic_url)

def set_app_config(app_config):
    _configmanager.app_config = app_config

" Default fields. Remember to add 'anything' to each index mapping "
defaultfields = _configmanager.defaultfields


def extra_src(mode, funcname, default):
    import importlib
    # If importing fails, try with a different path.
    _logger.debug('look for %s in %s' % (funcname, mode))
    _logger.debug('file: %s' % searchconfig[mode]['src'])
    try:
        classmodule = importlib.import_module(searchconfig[mode]['src'])
        _logger.debug('\n\ngo look in %s\n\n' % classmodule)
        func = getattr(classmodule, funcname)
        return func
    except Exception as e:
        _logger.debug('Could not find %s in %s', funcname, searchconfig[mode]['src'])
        _logger.debug(e)
        return default


def elastic(mode='', lexicon=''):
    return Elasticsearch(elasticnodes(mode=mode, lexicon=lexicon))


def searchconf(mode, field, failonerror=True):
    # looks up field in modes.json, eg. "autocomplete"
    # returns the karp field name (eg. baseform.raw)
    try:
        _logger.debug('\n%s\n' % searchconfig[mode])
        return searchconfig[mode][field]
    except Exception as e:
        if mode not in searchconfig:
            msg = "Mode %s not found" % mode
        else:
            msg = "Config field %s not found in mode %s" % (field, mode)
        _logger.error(msg+": ")
        _logger.exception(e)
        if failonerror:
            raise eh.KarpGeneralError(msg)
        return ''


def searchonefield(mode, field):
    # looks up field in modes.json, eg "autocomplete"
    # returns the first json path
    # TODO should change name to mode_one_field
    # TODO what to do if the field does not exist?
    # is probably handled elsewhere (searchconf or lookup_multiple)?
    return searchfield(mode, field)[0]


def searchfield(mode, field):
    # looks up field in modes.json, eg "autocomplete"
    # returns the json path
    fields = searchconf(mode, field)
    return sum([F.lookup_multiple(f, mode) for f in fields], [])


def all_searchfield(mode):
    # returns the json path of the field anything
    _logger.debug('%LOOK FOR ANYTHING\n')
    return F.lookup_multiple('anything', mode)


def mode_fields(mode):
    return searchconfig.get(mode, {})


def formatquery(mode, field, op):
    return searchconf(mode, 'format_query')(field, op)


def elasticnodes(mode='', lexicon=''):
    if not mode:
        mode = get_lexicon_mode(lexicon)
    return searchconf(mode, 'elastic_url')


def get_lexicon_suggindex(lexicon):
    mode = get_lexicon_mode(lexicon)
    sugg_index = searchconf(mode, 'suggestionalias')
    typ = searchconf(mode, 'type')
    return sugg_index, typ


def get_group_suggindex(mode):
    sugg_index = searchconf(mode, 'suggestionalias')
    typ = searchconf(mode, 'type')
    return sugg_index, typ


def get_lexicon_index(lexicon):
    mode = get_lexicon_mode(lexicon)
    index = searchconf(mode, 'indexalias')
    typ = searchconf(mode, 'type')
    return index, typ


def get_mode_type(mode):
    typ = searchconf(mode, 'type')
    return typ


def get_mode_index(mode):
    index = searchconf(mode, 'indexalias')
    typ = searchconf(mode, 'type')
    return index, typ


def get_mode_sql(mode):
    # dburl = 'mysql+pymysql://%s/%s?charset=utf8'
    dburl = _configmanager.app_config.DATABASE_BASEURL
    sql = searchconf(mode, 'sql', failonerror=False)
    if sql:
        return dburl.format(sql)
        # return dburl % (C.config['DB']['DBPASS'], sql)
    else:
        return None


def get_lexicon_sql(lexicon):
    mode = get_lexicon_mode(lexicon)
    return get_mode_sql(mode)


def get_lexiconlist(mode):
    lexiconlist = set()
    grouplist = [mode]
    modeconf = searchconfig.get(mode, {})
    for group in modeconf.get('groups', []):
        grouplist.append(group)
    for lex, lexconf in list(C.lexiconconfig.items()):
        if lexconf.get('mode', '') in grouplist:
            lexiconlist.add(lex)

    return list(lexiconlist)


def get_lexicon_mode(lexicon):
    try:
        return C.lexiconconfig[lexicon]['mode']
    except Exception:
        # TODO what to return
        _logger.warning("Lexicon %s not in conf" % lexicon)
        return ''
