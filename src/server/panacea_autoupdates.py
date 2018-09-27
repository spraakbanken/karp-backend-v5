import src.server.helper.configmanager as confM
from src.server.autoupdates import auto_update


@auto_update('panacea')
def add_lastmodified(obj, lex, actiontype, user, date):
    obj['lastmodified'] = date.strftime("%Y-%m-%dT%H:%M:%S")
    obj['lastmodifiedBy'] = user
    return obj

def seconds_since_epoch(date):
    """ Converts a datetime object to seconds since epoch.

    :param date: as a datetime.datetime object
    :returns: the date in seconds since epoch
    """
    return int(time.mktime(date.timetuple()))

@auto_update('panacea')
def annotatortimestamp(obj, lex, actiontype, user, date):
    import time
    obj['Annotator'] = user
    obj['Annotation_time'] = seconds_since_epoch(date)
    return obj
