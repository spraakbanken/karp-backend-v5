# -*- coding: utf-8 -*-
"""
Script for generating a file a list of with json objects,
to insert in Elastic Search
Input: xml (old_dalin/dalin.xml)
Only writtenForms, lemgrams and pos tags are marked up, the rest is left in
original format
Usage: cat inputfile.xml | python lexName lexOrder lmffile old_lemgrams.txt
           new_lemgrams.txt [extra.json] > outputfile.json
"""
import codecs
import sys
import json
import re
import xml.etree.ElementTree as etree
from os.path import isfile


def get_lemgrammapping(old, new):
    """ Reads two files of ordered lemgrams and creates a dictionary mapping
        the old version of the lemgram to the new version
        (usually sitta..e.1 => dalinm--sitta..vb.1)
    """
    oldmap = {}
    newlist = list(codecs.open(new, encoding='utf-8').readlines())
    for i, lem in enumerate(codecs.open(old, encoding='utf-8').readlines()):
        # prefix = 'dalinm--' if name=='dalin' else ''
        prefix = ''
        oldmap[lem.strip()] = prefix+newlist[i].strip()
        # oldmap[lem.strip()] = 'dalinm--'+newlist[i].strip()
    return oldmap


def get_lexicon(fil, name, lemgrammap, lexorder=15, make_bulk=True,
                bulk_info={}, extra=[], merge=''):
    """ Parse the xml
    """
    try:
        if type(fil) == str and not isfile(fil):
            root = etree.fromstring(fil)
        else:
            root = etree.parse(fil).getroot()
    except etree.ParseError as e:
        # Rasie SyntaxError to be caught by the backend
        raise SyntaxError('Xml invalid: %s' % str(e))

    if extra:
        # the extra file should contain a list of wellformed json objects
        try:
            extra = json.loads(open(extra).read())
        except ValueError as e:
            # Rasie SyntaxError to be caught by the backend
            raise SyntaxError('Extra information not wellformed: %s' % str(e))

    lmf_entries = {}
    if merge:
        lmf_entries = read_lmfjson(merge)

    # Return iterator of all entries
    lex_iterator = printLexicon(root, name, lexorder, lemgrammap,
                                make_bulk=make_bulk, bulk_info=bulk_info,
                                extra=extra, lmf_entries=lmf_entries)
    if not make_bulk:  # return the iterator
        return lex_iterator
    list(lex_iterator)  # force evaluating so that printing is done
    return ''


def read_lmfjson(filepath):
    lmf_entries = {}
    import lmftojson
    json_iterator = lmftojson.get_lexicon(filepath, name, lexorder=-1,
                                          make_bulk=False)
    for entry in json_iterator:
        entry = json.loads(entry["_source"])
        lemgram = entry["FormRepresentations"][0]["lemgram"]
        lmf_entries[lemgram] = entry
    return lmf_entries


def printLexicon(elem, name, lexorder, lemgrammap, make_bulk=True,
                 bulk_info={}, extra=[], lmf_entries={}):
    """ Prints the lexicon with each entry on one line, in json format
        If make_bulk is True, an index instruction is added before each entry
    """

    entries = 0
    index = bulk_info.get('index', "test")
    itype = bulk_info.get('type', "lexicalentry")
    # first add additional entries given in the extra file
    for e in extra:
        entries += 1
        e["lexiconName"] = name
        e["lexiconOrder"] = lexorder
        if make_bulk:  # print and verify
            print '{"index": {"_index": "%s", "_type": "%s"}}' % (index, itype)
            print json.dumps(e)
        else:
            yield e
    for e in elem:
        #  parse the xml
        if e.tag == "entry":
            this_entry = make_lexicalentry(e, name, lexorder, lemgrammap,
                                           lmf_entries=lmf_entries)
            if this_entry:
                entries += 1
                # print 'entry', make_bulk
                if make_bulk:
                    print '{"index": {"_index": "%s", "_type":"%s"}}' % (index,
                                                                         itype)
                    print json.dumps(this_entry)
                else:
                    # no bulk information ("_index" or "_type" is added here)
                    yield this_entry

    if not entries:
        # Raise syntaxerrror to be caught by the backend
        raise SyntaxError("No LexicalEntry in xml")


def make_lexicalentry(elem, name, lexorder, lemgrammap, lmf_entries={}):
    """ Creates and returns the json representation of an xml entry
    """
    lemgram = ''
    partofspeech = 'e'  # default
    for k, v in elem.attrib.items():  # get lemgram
        if k.endswith('}id'):
            oldlemgram = v
            lemgram = lemgrammap.get(v, '')
            oldname = oldlemgram.split('--')[-1].split('..')[0].strip('*?')
            if not lemgram:  # this is a word from dalin-supp
                lemgram = 'dalin-supp--'+oldlemgram
                print >> sys.stderr, 'not found', oldlemgram
            elif oldname.lower() != lemgram.split('--')[-1].split('..')[0]:
                print >> sys.stderr, 'unequal', oldlemgram, lemgram
    pos = re.search('.*\.\.(.*)\.\d', lemgram)
    if pos:
        partofspeech = pos.group(1)

    baseform = elem.find("./form/orth[@type='hw']").text.lower()
    xml = re.sub(re.escape(oldlemgram.encode('ascii', 'xmlcharrefreplace')),
                 lemgram, etree.tostring(elem)).replace('\n', '')
    wfs, sense_exs = [], []

    # Find all writtenForms
    for grandparent in elem.findall('.//orth/../..'):
        for parent in grandparent.findall('*'):
            for form in parent.findall('./orth'):
                tag = find_formtag(grandparent, parent, form)

                if tag != "hw":  # "hw" marks the baseform, extracted earlier
                    wf = 'writtenForm'
                    iscompound = re.search('\s*(re\s*//)?\s*cmpd\s*', tag)
                    if iscompound:
                        wf = 'text'
                    obj = {'tag': tag} if tag else {}
                    # if tag: obj = {'tag': tag}
                    # else:   obj = {}
                    use_form = ''
                    norm = form.attrib.get("norm", "")
                    if norm:
                        use_form = norm.lower()
                    elif not form.text:
                        print >> sys.stderr, "no form", lemgram, baseform
                    else:
                        use_form = form.text.lower()
                    if form.attrib.get("msd", ''):
                        obj['msd'] = form.attrib.get("msd")
                    if iscompound:
                        use_form = use_form.replace('~', '|')
                        obj['type'] = 'compound'
                    if use_form:
                        obj[wf] = use_form
                    sense_exs.append(obj) if iscompound else wfs.append(obj)

    formrep = {"lemgram": lemgram, "baseform": baseform}
    if partofspeech:
        formrep['partOfSpeech'] = partofspeech
        if lemgram == u'dalinm--rumpskatt..nn.1':
            print >> sys.stderr, 'setting', partofspeech

    doc = {"lexiconName": name, "lexiconOrder": str(lexorder),
           "FormRepresentations": [formrep], "WordForms": wfs, "xml": xml}
    if lemgram == u'dalinm--rumpskatt..nn.1':
        print >> sys.stderr, doc

    if sense_exs:
        doc['Sense'] = [{"SenseExamples": sense_exs}]
    if lemgram in lmf_entries:
        for field, val in lmf_entries[lemgram].items():
            if field == "FormRepresentations":
                add_form_rep(val, doc)
            elif field == "Sense":
                sense = doc.get("Sense", [])
                doc["Sense"] = sense+val
            elif field not in ["lexiconName", "lexiconOrder", "WordForms"]:
                if lemgram == u'dalinm--rumpskatt..nn.1':
                    print >> sys.stderr, 'last elif on ', field
                doc[field] = val

    if lemgram == u'dalinm--rumpskatt..nn.1':
        print >> sys.stderr, 'then', doc
    return doc


def add_form_rep(val, doc):
    for form_field in val:
        for form_field_name, form_val in form_field.items():
            if form_field_name not in ["lemgram", "baseform", "partOfSpeech"]:
                doc["FormRepresentations"][0][form_field_name] = form_val

    # written forms are found in:
    # 'form/orth', 're/form/orth', 'sense/form/orth', 'sense/re/form/orth',
    # 'sense/subsense/form/orth', 'sense/subsense/re/form/orth'
    # and 'subsense/re/form/orth'


def find_formtag(gp, p, form):
    # return the outmost type, which shows the relation to
    # the hw word (the baseform)
    if gp.attrib.get('type', '') and gp.tag in ['orth', 're', 'form']:
        return gp.get('type')
    if p.attrib.get('type', '') and gp.tag in ['orth', 're', 'form']:
        return p.attrib.get('type')
#    if form.attrib.get('type', ''):
    return form.attrib.get('type', '')


if __name__ == "__main__":
    lexicon = sys.stdin
    name = sys.argv[1]
    order = sys.argv[2]
    merge = sys.argv[3]
    lemmap = get_lemgrammapping(sys.argv[4], sys.argv[5])
    extra = []
    if len(sys.argv) > 6:
        extra = sys.argv[6]
    # print all entries in a list
    sep = '['
    for entry in get_lexicon(lexicon, name, lemmap, lexorder=order,
                             make_bulk=False, extra=extra, merge=merge):
        print sep
        print json.dumps(entry)
        sep = ','
    print ']'
