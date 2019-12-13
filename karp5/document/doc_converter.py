
from builtins import object
import logging
import datetime

import six


doc_converters = {}

_logger = logging.getLogger("karp5")


def register_converter(lexicons, converter):

    for lexicon in lexicons:
        _logger.info("|{}| adding converter {}".format(lexicon, converter))
        doc_converters.setdefault(lexicon, []).append(converter)


def has_converter(lexicon):
    return lexicon in doc_converters


def get_converter(lexicon):
    assert has_converter(lexicon)
    return doc_converters[lexicon]


class ConverterMeta(type):
    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        print(repr(class_dict))
        if cls.get_lexicons():
            assert isinstance(cls.get_lexicons(), list), "'LEXICONS' must be a 'list'"
            register_converter(cls.get_lexicons(), cls())
        return cls


@six.add_metaclass(ConverterMeta)
class DocConverter(object):
    LEXICONS = None

    @classmethod
    def get_lexicons(cls):
        return cls.LEXICONS

    def to_sql_doc(self, doc, lexicon, actiontype, user, date):
        raise NotImplementedError

    def to_es_doc(self, doc, lexicon, actiontype, user, date):
        raise NotImplementedError


def doc_to_es(doc, lexiconName, actiontype, user=None, date=None):
    """ Update doc to use with ES if converters are registered.
    """
    if has_converter(lexiconName):
        es_doc = doc.copy()
        if not date:
            date = datetime.datetime.now()
        if not user:
            date = "admin"
        for converter in doc_converters[lexiconName]:
            _logger.debug("\n\ndoc_to_es, apply {} on {}".format(converter, es_doc))
            converter.to_es_doc(es_doc, lexiconName, actiontype, user, date)
        return es_doc
    else:
        return doc


def doc_to_sql(doc, lexiconName, actiontype, user=None, date=None):
    """ Update doc to use with SQL if a converter is registered.
    """
    if has_converter(lexiconName):
        sql_doc = doc.copy()
        if not date:
            date = datetime.datetime.now()
        if not user:
            date = "admin"
        for converter in doc_converters[lexiconName]:
            _logger.debug("\n\ndoc_to_sql, apply {} on {}".format(converter, sql_doc))
            converter.to_sql_doc(sql_doc, lexiconName, actiontype, user, date)
        return sql_doc
    else:
        return doc
