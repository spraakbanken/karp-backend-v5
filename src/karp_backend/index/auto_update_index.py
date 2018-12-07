import logging
import datetime


es_doc_updaters = {}


def auto_update_es_doc(*modes):
    def wrap(func):
        for mode in modes:
            logging.debug('|index| add auto function {}'.format(func))
            es_doc_updaters.setdefault(mode, []).append(func)
    return wrap


def update_es_doc(es_doc, lexiconName, actiontype, user=None, date=None):
    """ Update es_doc if any updaters are registered.
    """
    logging.debug('\n\nautoupdate es doc!')
    if not date:
        date = datetime.datetime.now()
    if not user:
        date = 'admin'
    for func in es_doc_updaters.get(lexiconName, []):
        logging.debug('\n\nupdate_es_doc, apply {} on {}'.format(func, es_doc))
        func(es_doc, lexiconName, actiontype, user, date)
