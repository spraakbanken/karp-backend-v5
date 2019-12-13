# coding: utf-8
# from karp5.config import mgr as conf_mgr
import copy
import json
from re import findall
import sys
import unicodedata

from karp5.config import mgr as conf_mgr
from karp5 import errors

# lexiconconf = conf_mgr.lexicons


def validate_json(doc, lexicon):
    for key, val in doc.items():
        if key == "xml":
            doc[key] = validate_xml(val, lexicon)
        elif conf_mgr.lexicons.get(lexicon, {}).get("no_escape"):
            continue
        else:
            doc[key] = checkelem(val, lexicon)


def checkelem(elem, lexicon):
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
        return escape(elem)
    if isinstance(elem, dict):
        # recursive call for objects
        validate_json(elem, lexicon)
        return elem
    if isinstance(elem, list):
        # recursiv call for elements of lists
        for i, e in enumerate(elem):
            elem[i] = checkelem(e, lexicon)
    # return numbers, checked list etc
    return elem


def validate_xml(xml, lexicon):
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
            if tag not in conf_mgr.lexicons.get(lexicon).get("usedtags", []):
                # raise Exception('Data contains unapproved tags: %s' % tag)
                raise errors.KarpParsingError("Data contains unapproved tags: %s" % tag)
    elif isinstance(xml, list):
        for i, xml_e in enumerate(xml):
            xml[i] = validate_xml(xml_e, lexicon)
    else:
        checkelem(xml, lexicon)
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


# For testing
def compare(orig, obj):
    if isinstance(orig, str) or isinstance(obj, str):
        # check that strings are escaped but otherwise unchanged
        if escape(orig) != obj:
            raise Exception("Unequal %s %s" % (orig, obj))

    elif len(orig) != len(obj):
        # all other types of objects should have unchanged length
        raise Exception("Unequal length %s %s" % (orig, obj))

    # recursively check the rest
    if isinstance(orig, dict):
        for key, val in orig.items():
            compare(val, obj[key])
    elif isinstance(orig, list):
        for i, val in enumerate(orig):
            compare(val, obj[i])
    elif orig != obj:
        raise Exception("Unequal %s %s" % (orig, obj))


if __name__ == "__main__":
    for fil in sys.argv[1:]:
        print("read", fil)
        objs = json.loads(open(fil).read())
        for i, obj in enumerate(objs):
            orig = copy.deepcopy(obj)
            validate_json(obj, "saldo")
            compare(orig, obj)
        print("%d objects tested, OK" % (i + 1))
