import src.server.helper.configmanager as confM
from src.server.autoupdates import auto_update


@auto_update('skbl', 'saol', 'hellqvist', 'term-swefin', 'konstruktikon-rus',
             'konstruktikon-multi','konstruktikon')
def add_lastmodified(obj, lex, actiontype, user, date):
    obj['lastmodified'] = date.strftime("%Y-%m-%dT%H:%M:%S")
    obj['lastmodifiedBy'] = user
    return obj


@auto_update('skbl', 'saol', 'hellqvist', 'term-swefin', 'konstruktikon-rus',
             'konstruktikon-multi','konstruktikon')
def set_lexiconOrder(obj, lex, actiontype, user, date):
    lexname = obj['lexiconName']
    lexOrder = confM.lexiconconfig[lexname]['order']
    obj['lexiconOrder'] = lexOrder
