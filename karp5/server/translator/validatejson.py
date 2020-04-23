# coding: utf-8
# from karp5.config import mgr as conf_mgr
from re import findall
from typing import Dict
import unicodedata

from karp5.config import conf_mgr
from karp5 import errors

# lexiconconf = conf_mgr.lexicons


def validate_json(doc: Dict, lexicon_id: str):
    no_escape = conf_mgr.lexicons.get(lexicon_id, {}).get("no_escape", False)
    return validate_dict(doc, lexicon_id, no_escape=no_escape)


def validate_dict(doc: Dict, lexicon_id: str, *, no_escape: bool) -> None:
    for key, val in doc.items():
        if key == "xml":
            doc[key] = validate_xml(val, lexicon_id, no_escape=no_escape)
        else:
            doc[key] = checkelem(val, lexicon_id, no_escape=no_escape)


def checkelem(elem, lexicon_id: str, *, no_escape: bool):
    # checks different types of elements
    # and then returns the element
    # if it is a string, it will be returned escaped
    # lists are returned with all its elements checked/escaped
    # other types (numbers, bools) are just returned
    if isinstance(elem, str):
        # normalize unicode characters
        # 'o\u0308' >>> u'\xf6'
        elem = unicodedata.normalize("NFC", elem)
        # strings are escaped
        if no_escape:
            return elem
        return escape(elem)
    if isinstance(elem, dict):
        # recursive call for objects
        validate_dict(elem, lexicon_id, no_escape=no_escape)
        return elem
    if isinstance(elem, list):
        # recursiv call for elements of lists
        for i, e in enumerate(elem):
            elem[i] = checkelem(e, lexicon_id, no_escape=no_escape)
    # return numbers, checked list etc
    return elem


def validate_xml(xml, lexicon_id: str, *, no_escape: bool):
    # checks that the field only contains accepted tags, as specified
    # in the lexicon configurations
    # TODO this will escape tags if they're embedded in other objects
    # "xml" : "<tag>"  ==> "xml" : "<tag>"
    # "xml" : ["<tag>"]  ==> "xml" : ["<tag>"]
    # but
    # "xml" : {"text" : "<tag>"}  ==> "xml" : {"text : "&lt;tag&gt;"}
    # check with jonatan if that's ok for front end

    # check that no unaccepted tags are present
    if isinstance(xml, str):
        for tag, attrs in findall(r"<\/?\s*(\S*?)(\s+.*?)?>", xml):
            print(f"tag = {tag}, attrs = {attrs}")
            print(f"usedtags = {conf_mgr.lexicons.get(lexicon_id).get('usedtags', [])}")
            if tag not in conf_mgr.lexicons.get(lexicon_id).get("usedtags", []):
                # raise Exception('Data contains unapproved tags: %s' % tag)
                raise errors.KarpParsingError("Data contains unapproved tags: %s" % tag)
    elif isinstance(xml, list):
        for i, xml_e in enumerate(xml):
            xml[i] = validate_xml(xml_e, lexicon_id, no_escape=no_escape)
    else:
        validate_dict(xml, lexicon_id, no_escape=no_escape)
    return xml


def escape(s):
    s = unescape(s)  # avoid double escaping
    s = s.replace("&", "&amp;")
    s = s.replace("'", "&apos;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s.replace('"', "&quot;")


def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s
