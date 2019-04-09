from __future__ import unicode_literals
from builtins import object
import json
import logging
import os
import re
import copy
import sys

from elasticsearch import Elasticsearch

import six

# import karp5.server.helper.configpaths as C
from karp5 import errors
# from karp5.server.translator
from karp5.instance_info import get_instance_path
from .errors import KarpConfigException
from karp5.util.debug import print_err


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


# configdir = os.path.join(get_instance_path(), 'config')

def complement_dict(adict, bdict):
    " Adds values from bdict into adict unless the key is already there "
    for key, val in bdict.items():
        if key not in adict:
            adict[key] = val


def merge_dict(adict, bdict):
    " Merges bdict into adict by taking the union of the vaule lists "
    for key, val in bdict.items():
        if key in adict:
            adict[key] = list(set(adict[key]) | set(val))
        else:
            adict[key] = val


def load_from_file(
        path,
        default={}
        ):
    try:
        with open(path) as fp:
            return json.load(fp)
    except Exception as e:
        print_err("Error when loading '{}':".format(path))
        print_err(e)

    return default


class ConfigManager(object):
    def __init__(self):
        self.modes = {}
        self.config = {}
        self.lexicons = {}
        self.field = {}
        self.defaultfields = {}
        self.app_config = None
        self.configdir = os.path.join(get_instance_path(), 'config')
        self._extra_src = {}
        self.load_config()

    def add_extra_src(self, mode, func):
        mode_fun_map = self._extra_src.get(mode, {})
        if func.__name__ in mode_fun_map:
            print_err("""WARNING!
                Function '{}' is already registered for mode '{}'. Overwritting...""".format(
                    func.__name__,
                    mode
                )
            )

        mode_fun_map[func.__name__] = func
        self._extra_src[mode] = mode_fun_map

    def load_config(self):
        self.modes = load_from_file(
            os.path.join(self.configdir, 'modes.json')
        )
        set_defaults(self.modes)

        self.lexicons = load_from_file(
            os.path.join(self.configdir, 'lexiconconf.json')
        )
        set_defaults(self.lexicons)

        self.config = load_from_file(
            os.path.join(self.configdir, 'config.json')
        )

        self.defaultfields = load_from_file(
            os.path.join(self.configdir, 'mappings/fieldmappings_default.json')
        )

        # with open(os.path.join(self.configdir, 'fieldmappings.json')) as fp:
        #     self.fields = json.load(fp)
        self.fields = self.read_fieldmappings()

    def read_fieldmappings(self):
        fields = {}
        for mode in self.modes.keys():
            fields[mode] = self.read_fieldmappings_mode(mode)
        return fields

    def read_fieldmappings_mode(self, mode):
        " Open a mode's config file and combine them "
        # " Default fields. Remember to add 'anything' to each index mapping "
        # defaultfields = _configmanager.defaultfields
        default_fields = copy.deepcopy(self.defaultfields)
        # step through the group members if the mode is an aliasmode
        # or use it's own config file if it's a indexmode
        all_fields = {}
        # print("create mode '{}'".format(mode))
        for index in self.modes[mode].get('groups', [mode]):
            try:
                # print("reading fieldmappings for index '{}'".format(index))
                with open(os.path.join(
                    self.configdir, 'mappings/fieldmappings_{}.json'.format(index))
                ) as fp:
                    fields = json.load(fp)
                merge_dict(all_fields, fields)
            except IOError:
                msg = "Couldn't find fieldmappings for mode '{}'".format(index)
                # print(msg)
                raise KarpConfigException(msg)

        complement_dict(all_fields, default_fields)
        return all_fields

    def override_elastic_url(self, elastic_url):
        for mode, mode_settings in six.viewitems(self.modes):
            mode_settings['elastic_url'] = elastic_url

    def get_mode_sql(self, mode):
        # dburl = 'mysql+pymysql://%s/%s?charset=utf8'
        dburl = self.app_config.DATABASE_BASEURL
        sql = self.searchconf(mode, 'sql', failonerror=False)
        if sql:
            return dburl.format(sql)
            # return dburl % (C.config['DB']['DBPASS'], sql)
        else:
            return None

    def searchconf(self, mode, field, failonerror=True):
        # looks up field in modes.json, eg. "autocomplete"
        # returns the karp field name (eg. baseform.raw)
        try:
            _logger.debug('\n%s\n' % self.modes[mode])
            return self.modes[mode][field]
        except Exception as e:
            if mode not in self.modes:
                msg = "Mode '%s' not found" % mode
            else:
                msg = "Config field '%s' not found in mode '%s'" % (field, mode)
            _logger.error(msg+": ")
            _logger.exception(e)
            if failonerror:
                raise errors.KarpGeneralError(msg)
            return

    def extra_src(self, mode, funcname, default):
        # Try in new way first
        mode_fun_map = self._extra_src.get(mode)
        if mode_fun_map:
            func = mode_fun_map.get(funcname)
            if func:
                _logger.debug("Found function '{}' for mode '{}'".format(funcname, mode))
                return func
            else:
                _logger.debug("Didn't find function '{}' for mode '{}'".format(funcname, mode))
        else:
            _logger.debug("Didn't find a function_map for mode '{}'".format(mode))

        # Then use old way
        import importlib
        # If importing fails, try with a different path.
        _logger.debug('look for %s in %s' % (funcname, mode))
        if mode not in self.modes:
            _logger.debug("Can't find mode '{}' in modes".format(mode))
        _logger.debug('sys.path = {}'.format(sys.path))
        _logger.debug('file: %s' % self.modes[mode]['src'])
        try:
            classmodule = importlib.import_module(self.modes[mode]['src'])
            _logger.debug('\n\ngo look in %s\n\n' % classmodule)
            func = getattr(classmodule, funcname)
            return func
        except Exception as e:
            _logger.debug('Could not find %s in %s', funcname, self.modes[mode]['src'])
            _logger.debug(e)
            return default

    def elastic(self, mode='', lexicon=''):
        return Elasticsearch(self.elasticnodes(mode=mode, lexicon=lexicon))

    def searchonefield(self, mode, field):
        # looks up field in modes.json, eg "autocomplete"
        # returns the first json path
        # TODO should change name to mode_one_field
        # TODO what to do if the field does not exist?
        # is probably handled elsewhere (searchconf or lookup_multiple)?
        return self.searchfield(mode, field)[0]

    def searchfield(self, mode, field):
        # looks up field in modes.json, eg "autocomplete"
        # returns the json path
        _logger.info("Looking for '{}' in '{}'".format(field, mode))
        fields = self.searchconf(mode, field)
        _logger.info("Found '{}' => '{}'".format(field, fields))
        return sum([self.lookup_multiple(f, mode) for f in fields], [])

    def all_searchfield(self, mode):
        # returns the json path of the field anything
        _logger.debug('%LOOK FOR ANYTHING\n')
        return self.lookup_multiple('anything', mode)

    def mode_fields(self, mode):
        return self.modes.get(mode, {})

    def formatquery(self, mode, field, op):
        return self.searchconf(mode, 'format_query')(field, op)

    def elasticnodes(self, mode='', lexicon=''):
        if not mode:
            mode = self.get_lexicon_mode(lexicon)

        if self.app_config.OVERRIDE_ELASTICSEARCH_URL or 'elastic_url' not in self.modes[mode]:
            return self.app_config.ELASTICSEARCH_URL
        else:
            return self.modes[mode]['elastic_url']

    def get_lexicon_suggindex(self, lexicon):
        mode = self.get_lexicon_mode(lexicon)
        sugg_index = self.searchconf(mode, 'suggestionalias')
        typ = self.searchconf(mode, 'type')
        return sugg_index, typ

    def get_group_suggindex(self, mode):
        sugg_index = self.searchconf(mode, 'suggestionalias')
        typ = self.searchconf(mode, 'type')
        return sugg_index, typ

    def get_lexicon_index(self, lexicon):
        mode = self.get_lexicon_mode(lexicon)
        index = self.searchconf(mode, 'indexalias')
        typ = self.searchconf(mode, 'type')
        return index, typ

    def get_mode_type(self, mode):
        return self.searchconf(mode, 'type')

    def get_mode_index(self, mode):
        index = self.searchconf(mode, 'indexalias')
        typ = self.searchconf(mode, 'type')
        return index, typ

    def get_lexicon_sql(self, lexicon):
        mode = self.get_lexicon_mode(lexicon)
        return self.get_mode_sql(mode)

    def get_lexiconlist(self, mode):
        lexiconlist = set()
        grouplist = [mode]
        modeconf = self.modes.get(mode, {})
        for group in modeconf.get('groups', []):
            grouplist.append(group)
        for lex, lexconf in self.lexicons.items():
            if lexconf.get('mode', '') in grouplist:
                lexiconlist.add(lex)

        return list(lexiconlist)

    def get_modes_that_include_mode(self, mode):
        modes = set()
        modes.add(mode)
        for name, info in self.modes.items():
            if mode in info.get('groups', []):
                modes.add(name)
        return list(modes)

    def get_lexicon_mode(self, lexicon):
        try:
            return self.lexicons[lexicon]['mode']
        except Exception:
            # TODO what to return
            _logger.warning("Lexicon %s not in conf" % lexicon)
            return ''

    def get_mapping(self, index):
        filepath = 'mappings/mappingconf_{}.json'.format(index)
        try:
            with open(os.path.join(self.configdir, filepath)) as fp:
                return fp.read()
        except Exception:
            raise KarpConfigException(
                "Can't find mappingconf for index '{}'".format(index)
            )

    def lookup(self, field, mode, own_fields={}):
        # standardmode = C.config['SETUP']['STANDARDMODE']
        # def lookup(self, field, mode=standardmode, own_fields={}):
        return self.lookup_spec(field, mode, own_fields=own_fields)[0]

    def lookup_spec(self, field, mode, own_fields={}):
        # def lookup_spec(self, field, mode=standardmode, own_fields={}):
        try:
            val = self.get_value(field, mode, own_fields=own_fields)
            if type(val) is dict:
                return ([val["search"]], (val["path"], val["typefield"], val["type"]))
            else:
                return (val[0],)
        except Exception as e:
            msg = "Field '%s' not found in mode '%s'" % (field, mode)
            _logger.error(msg+": ")
            _logger.exception(e)
            raise errors.KarpGeneralError(msg)

    def lookup_multiple_spec(self, field, mode):
        # def lookup_multiple_spec(self, field, mode=standardmode):
        try:
            val = self.get_value(field, mode)
            if type(val) is dict:
                return ([val["search"]], (val["path"], val["typefield"], val["type"]))
            else:
                return (val, '')
        except Exception as e:
            msg = "Field '%s' not found in mode '%s'" % (field, mode)
            _logger.error(msg+": ")
            _logger.exception(e)
            raise errors.KarpGeneralError(msg)

    def lookup_multiple(self, field, mode):
        # def lookup_multiple(self, field, mode=standardmode):
        _logger.info("Lookup '{}' in '{}'".format(field, mode))
        return self.lookup_multiple_spec(field, mode)[0]

    def get_value(self, field, mode, own_fields=None):
        if own_fields:
            use_fields = own_fields
        else:
            use_fields = self.fields
        mappings = use_fields.get(mode, {})
        _logger.info('mappings = {}'.format(mappings))
        group = re.search('(.*)((.bucket)|(.search)|(.sort))$', field)
        if field in mappings:
            return mappings[field]
        elif group is not None:
            return self.get_value(group.group(1), mode, own_fields=own_fields)
        else:
            msg = ("Could not find field '%s' for mode '%s', '%s'"
                   % (field, mode, mappings))
            _logger.debug(msg)
            raise KarpConfigException(msg, debug_msg=msg+"\n%s" % mappings)
