import json
import logging
import re
import os
import karp_backend.server.errorhandler as eh
import karp_backend.server.helper.configpaths as C
from karp_backend.instance_info import get_instance_path


absolute_path = C.config['SETUP']['ABSOLUTE_PATH']
try:
    with open(os.path.join(get_instance_path(), 'config/fieldmappings.json')) as fp:
        fields = json.load(fp)
except Exception as e:
    logging.exception(e)
standardmode = C.config['SETUP']['STANDARDMODE']


def lookup(field, mode=standardmode, own_fields={}):
    return lookup_spec(field, mode, own_fields=own_fields)[0]


def lookup_spec(field, mode=standardmode, own_fields={}):
    try:
        val = get_value(field, mode, own_fields=own_fields)
        if type(val) is dict:
            return ([val["search"]], (val["path"], val["typefield"], val["type"]))
        else:
            return (val[0],)
    except Exception as e:
        msg = "Field %s not found in mode %s" % (field, mode)
        logging.error(msg+": ")
        logging.exception(e)
        raise eh.KarpGeneralError(msg)


def lookup_multiple_spec(field, mode=standardmode):
    try:
        val = get_value(field, mode)
        if type(val) is dict:
            return ([val["search"]], (val["path"], val["typefield"], val["type"]))
        else:
            return (val, '')
    except Exception as e:
        msg = "Field %s not found in mode %s" % (field, mode)
        logging.error(msg+": ")
        logging.exception(e)
        raise eh.KarpGeneralError(msg)


def lookup_multiple(field, mode=standardmode):
    return lookup_multiple_spec(field, mode)[0]


def get_value(field, mode, own_fields=''):
    if own_fields:
        use_fields = own_fields
    else:
        use_fields = fields
    mappings = use_fields.get(mode, {})
    group = re.search('(.*)((.bucket)|(.search)|(.sort))$', field)
    if field in mappings:
        return mappings[field]
    elif group is not None:
        return get_value(group.group(1), mode, own_fields=own_fields)
    else:
        import parsererror as PErr
        msg = ("Could not find field %s for mode %s, %s"
               % (field, mode, mappings))
        logging.debug(msg)
        raise PErr.QueryError(msg, debug_msg=msg+"\n%s" % mappings)
