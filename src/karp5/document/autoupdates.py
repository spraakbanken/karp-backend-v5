import datetime
import logging


auto_updates = {}
auto_updates_child = {}

_logger = logging.getLogger("karp5")


def auto_update_child(*modes):
    def wrap(func):
        for mode in modes:
            _logger.debug("add child auto function %s" % func)
            auto_updates_child.setdefault(mode, []).append(func)
        return func

    return wrap


def auto_update(*modes):
    def wrap(func):
        for mode in modes:
            _logger.debug("add auto function %s" % func)
            auto_updates.setdefault(mode, []).append(func)
        return func

    return wrap


def auto_update_document(data_doc, lexiconName, actiontype, user, date):
    _logger.debug("\n\nautoupdate!")
    if not date:
        date = datetime.datetime.now()
    for func in auto_updates.get(lexiconName, []):
        _logger.debug("\n\nautoupdate, apply %s on %s" % (func, data_doc))
        func(data_doc, lexiconName, actiontype, user, date)


def autoupdate_child(child, parent, lexicon, user, date=""):
    _logger.debug("autoupdate child")
    if not date:
        date = datetime.datetime.now()
    for func in auto_updates_child.get(lexicon, []):
        _logger.debug("autoupdate_child, apply %s on %s", func, child)
        func(child, parent, lexicon, user, date)
