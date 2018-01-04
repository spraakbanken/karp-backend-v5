from elasticsearch import Elasticsearch
import logging
import src.server.helper.configpaths as C
import src.server.errorhandler as eh
from src.server.translator import fieldmapping as F


searchconfig = C.searchconfig
config = C.config
lexiconconfig = C.lexiconconfig
setupconfig = config['SETUP']

defaultmode = searchconfig.get('default', {})
for mode, vals in searchconfig.items():
    if mode != 'default':
          for key, val in defaultmode.items():
              if key not in vals:
                  vals[key] = val


defaultmode = lexiconconfig.get('default', {})
for mode, vals in lexiconconfig.items():
    if mode != 'default':
          for key, val in defaultmode.items():
              if key not in vals:
                  vals[key] = val


" Default fields. Remember to add 'anything' to each index mapping "
defaultfields = {
    "_score": ['_score'],
    "anything": ['_all'],
    "id": ['_id'],
    "lexiconName": ['lexiconName'],
    "lexiconName.bucket": ['lexiconName'],
    "resource": ['lexiconName'],
    "lexiconOrder": ['lexiconOrder'],
    "lastmodifiedBy": ['lastmodifiedBy'],
    "lastmodified.bucket" : ["lastmodified.raw"],
    "lastmodified": ['lastmodified']
}


def extra_src(mode, funcname, default):
    import importlib
    # If importing fails, try with a different path.
    try:
        classmodule = importlib.import_module(C.searchconfig[mode]['src'])
        logging.debug('\n\ngo look in %s\n\n' % classmodule)
        func = getattr(classmodule, funcname)
        return func
    except:
        #raise
        return default


def elastic(mode='', lexicon=''):
    return Elasticsearch(elasticnodes(mode=mode, lexicon=lexicon))


def searchconf(mode, field, failonerror=True):
    # looks up field in modes.json, eg. "autocomplete"
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


def mode_fields(mode):
    return C.searchconfig.get(mode, {})


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
    dburl = 'mysql+pymysql://%s/%s?charset=utf8'
    sql = searchconf(mode, 'sql', failonerror=False)
    if sql:
        return dburl % (C.config['DB']['DBPASS'], sql)
    else:
        return False


def get_lexicon_sql(lexicon):
    mode = get_lexicon_mode(lexicon)
    return get_mode_sql(mode)


def get_lexiconlist(mode):
    lexiconlist = set()
    grouplist = [mode]
    modeconf = C.searchconfig.get(mode, {})
    for group in modeconf.get('groups', []):
        grouplist.append(group)
    for lex, lexconf in C.lexiconconfig.items():
        if lexconf[0] in grouplist:
            lexiconlist.add(lex)

    return list(lexiconlist)


def get_lexicon_mode(lexicon):
    try:
        return C.lexiconconfig[lexicon][0]
    except Exception:
        # TODO what to return
        logging.warning("Lexicon %s not in conf" % lexicon)
        return ''


def lookup_op(field, mode='karp'):
    " Checks if there are special conditions for this field "
    specials = searchconf(mode, 'special_fields', failonerror=False) or {}
    return specials.get(field, {})
