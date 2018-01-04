import json
import logging
import re
import src.server.errorhandler as eh
import src.server.helper.configpaths as C


absolute_path = C.config['SETUP']['ABSOLUTE_PATH']
try:
    fields = json.load(open(absolute_path+'/config/fieldmappings.json'))
except Exception as e:
    logging.exception(e)


def lookup(field, mode='karp', own_fields={}):
    return lookup_spec(field, mode, own_fields=own_fields)[0]


def lookup_spec(field, mode='karp', own_fields={}):
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


def lookup_multiple_spec(field, mode='karp'):
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


def lookup_multiple(field, mode='karp'):
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
    elif field in default:
        return default[field]
    else:
        import parsererror as PErr
        msg = ("Could not find field %s for mode %s, %s"
               % (field, mode, mappings))
        logging.debug(msg)
        raise PErr.QueryError(msg, debug_msg=msg+"\n%s" % mappings)
