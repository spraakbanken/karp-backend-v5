import config.extra_src
import config.dbconf as dbconf
import config.lexiconconf as lexiconconf
import config.modes
from elasticsearch import Elasticsearch
import logging
import src.server.errorhandler as eh
from src.server.translator import fieldmapping as F

searchconfig = {}
for mode, mode_dict in config.modes.modes.items():
    searchconfig[mode] = mode_dict


def elastic(mode='', lexicon=''):
    return Elasticsearch(elasticnodes(mode=mode, lexicon=lexicon))


def extra_src(mode, funcname, default):
    return config.extra_src.extra_src().get(mode, {}).get(funcname, default)


def searchconf(mode, field, failonerror=True):
    # looks up field in modes.py, eg. "autocomplete"
    # returns the karp field name (eg. baseform.raw)
    try:
        return searchconfig[mode][field]
    except Exception as e:
        if mode not in searchconfig:
            msg = "Mode %s not found" % mode
        else:
            msg = "Config field %s not found in mode %s" % (field, mode)
        logging.error(msg+": ")
        logging.exception(e)
        if failonerror:
            raise eh.KarpGeneralError(msg)
        return ''


def searchonefield(mode, field):
    # looks up field in modes.py, eg "autocomplete"
    # returns the first json path
    # TODO should change name to mode_one_field
    # TODO what to do if the field does not exist?
    # is probably handled elsewhere (searchconf or lookup_multiple)?
    return searchfield(mode, field)[0]


def searchfield(mode, field):
    # looks up field in modes.py, eg "autocomplete"
    # returns the json path
    fields = searchconf(mode, field)
    return sum([F.lookup_multiple(f, mode) for f in fields], [])


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
    sql = searchconf(mode, 'sql', failonerror=False)
    if sql:
        return dbconf.dburl % sql
    else:
        return False


def get_lexicon_sql(lexicon):
    mode = get_lexicon_mode(lexicon)
    return get_mode_sql(mode)


def get_lexiconlist(mode):
    lexiconlist = set()
    grouplist = [mode]
    modeconf = config.modes.modes.get(mode, {})
    for group in modeconf.get('groups', []):
        grouplist.append(group)
    for lex, lexconf in lexiconconf.conf.items():
        if lexconf[0] in grouplist:
            lexiconlist.add(lex)

    return list(lexiconlist)


def get_lexicon_mode(lexicon):
    try:
        return lexiconconf.conf[lexicon][0]
    except Exception:
        # TODO what to return
        logging.warning("Lexicon %s not in conf" % lexicon)
        return ''


def lookup_op(field, mode='karp'):
    " Checks if there are special conditions for this field "
    specials = searchconf(mode, 'special_fields', failonerror=False) or {}
    return specials.get(field, {})
