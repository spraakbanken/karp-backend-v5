# -*- coding: utf-8 -*-
"""
Script for generating a file with json objects in bulk format,
to insert in Elastic Search
Input: lmf, xml
Some structures are changed in order to homogenize the lexica
Usage: cat inputfile.xml | python lexName > outputfile.json
"""
import jsonlib as jl
# import collections
from os.path import isfile
import re
import pycountry  # pip install pycountry
from saldo_paths import get_relations
import sys
import xml.etree.ElementTree as etree


def get_lexicon(fil, name, lexorder=-1, make_bulk=True, return_bulk=False,
                bulk_info={}):
    try:
        if type(fil) == str and not isfile(fil):
            root = etree.fromstring(fil)
        else:
            print('read', fil)
            root = etree.parse(fil).getroot()
    except etree.ParseError as e:
        # Use SyntaxError so that the backend catches it
        raise SyntaxError('Xml invalid: %s' % str(e))

    kids = {}
    if name == "saldo":
        # For saldo, add all children to the sense relations.
        kids,  paths = get_relations(fil)

    lexfunc = {'lexin': lexin,
               'lwt': lwt,
               'bliss': bliss,
               'bliss_char': bliss,
               'blingbring': blingbring,
               'konstruktikon': konstruktikon,
               'konstruktikon-rus': konstruktikon,
               'konstruktikon-multi': konstruktikon_multi,
               'swefn': swefn,
               'saldo': saldo,
               'saldom': saldom,
               'saldoe': saldoe,
               'dalin': dalin,
               'dalinm': saldom,
               'schlyter': schlyter,
               'soederwall': soederwall,
               'soederwall-supp': soederwallsupp,
               'swedberg': swedberg,
               'fsvm': saldom, 'ao': ao,
               'dalin-base': dalinbase,
               'diapivot': diapivot,
               'hellqvist': hellqvist,
               'kelly': kelly,
               'parolelexplus': parole,
               'simpleplus': simple,
               'wordnet-saldo': wordnet,
               'swedbergm': saldom,
               'swesaurus': swesaurus,
               'term-swefin': termswefin,
               'term-finswe': termswefin
               }

    for elem in root:
        if elem.tag == "Lexicon":
            # Return iterator of all LexicalEntries
            lex_iterator = printLexicon_spec(elem, lexfunc[name], name,
                                             lexorder, kids=kids,
                                             make_bulk=make_bulk,
                                             return_bulk=return_bulk,
                                             bulk_info=bulk_info)
            if not make_bulk:
                return lex_iterator
            list(lex_iterator)  # force evaluating so that printing is done
            return ''


def printLexicon_spec(elem, lexfunc, lexname, lexorder, make_bulk=True,
                      return_bulk=False, bulk_info={}, kids={}):
    """ Prints the lexicon with each entry on one line, in json format
        Before each line an index instruction is added
    """

    entries = 0
    try:
        for e in elem:
            if e.tag == "LexicalEntry":
                index = bulk_info.get('index', "test")
                itype = bulk_info.get('type', "lexicalentry")
                if make_bulk:
                    print('{"index" : {"_index" : "%s", "_type" : "%s"}}'
                          % (index, itype))
                allentries = lexfunc(e, lexname, lexorder, kids=kids)
                if allentries:
                    entries += 1
                    if make_bulk:
                        print(allentries)
                    if return_bulk:
                        yield allentries

                    elif not return_bulk or make_bulk:
                        yield {"_index": index, "_type": itype,
                               "_source": allentries}
                    else:
                        print('No json generated', etree.tostring(e))

    except Exception:
        print(etree.tostring(e))
        raise

    if not entries:
        # Raise syntaxerrror for backend to catch
        raise SyntaxError("No LexicalEntry in xml")


def ao(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    fr = jl.FormRepresentation()
    form = entry.find('./Lemma/FormRepresentation')
    jl.add_feature(form, fr, 'baseform', 'writtenForm')
    jl.add_features(form, fr, ['lemgram', 'partOfSpeech', 'nativePartOfSpeech',
                               'rank'])
    le.lemma.add_form_representation(fr)

    sense = jl.Sense(entry.find('Sense').get('id'))
    le.add_sense(sense)

    return unicode(le)


def blingbring(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    fr = jl.FormRepresentation()
    form = entry.find('./Lemma/FormRepresentation')
    jl.add_feature(form, fr, 'baseform', 'writtenForm')

    roget = jl.BlingBringRoget(jl.findfeat(form, 'roget_head_id'))
    bring = jl.BlingBringBring(jl.findfeat(form, 'bring_entry_id'))
    fr.add_object(roget)
    fr.add_object(bring)
    le.lemma.add_form_representation(fr)

    for senseentry in entry.findall('Sense'):
        sense = jl.Sense(senseentry.get('id'))
        le.add_sense(sense)

    return unicode(le)


def bliss(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    fr = jl.FormRepresentation()
    form = entry.find('./Lemma/FormRepresentation')
    jl.add_features(form, fr, ['gloss', 'blissID', 'symbolType', 'BCI_AV'])

    le.lemma.add_form_representation(fr)

    for c in entry.find("ListOfComponents").findall("Component"):
        le.add_component(jl.Component(c.get('entry')))

    # Sense ids are excluded, since they provide no new information
    # sense = jl.Sense(entry.find('Sense').get('id'))
    # le.add_sense(sense)

    le.add_saldoLinks(get_saldo_links(entry))
    # jl.add_features(entry, le, ['symbolWidth', 'symbolHeight', 'symbolPath',
    #                            'symbolCenter'])
    return unicode(le)


def konstruktikon_multi(entry, name, order, kids={}):
    return konstruktikon(entry, name, order, kids=kids, cxn_lang=True)


def konstruktikon(entry, name, order, kids={}, cxn_lang=False):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    single_topfeatures = ['lastmodified', 'lastmodifiedBy']
    jl.add_features(entry, le, single_topfeatures)

    senses = entry.findall('Sense')
    single_features = ['BCxnID', 'cat', 'comment', 'createdBy', 'entry_status',
                       'illustration', 'structure']
    # reference is single for SweCxn but multiple for RusCxn
    multiple_features = ['coll', 'type', 'inheritance', 'cee', 'evokes',
                         'internal_comment', 'reference', 'other_examples',
                         'sweccnLink']

    if cxn_lang:
        for key, val in entry.attrib.items():
            if key.endswith('lang'):
                lang = val
        le.add_feature(jl.Feature("cxn_lang", lang))

    for sense_entry in senses:
        sense = jl.Sense(sense_entry.attrib.get('id'))
        jl.add_features(sense_entry, sense, single_features)
        for feat in multiple_features:
            jl.add_feature(sense_entry, sense, feat)

        # namespaces causes 'find' etc. to not work
        for elem in sense_entry:
            if elem.tag.split('}')[-1] == "int_const_elem":
                sense.add_int_const_elems(elem.attrib.items())
            if elem.tag.split('}')[-1] == "ext_const_elem":
                sense.add_ext_const_elems(elem.attrib.items())
            if elem.tag.split('}')[-1] == "example":
                xml = print_konstruktikon_xml(elem)
                sense.add_example_xml(xml)

            elif elem.tag.split('}')[-1] == "definition":
                lang = ''
                to_remove = []
                for key, val in elem.attrib.items():
                    if key.endswith('}lang'):
                        lang = val
                        to_remove.append(key)
                for key in to_remove:
                    del elem.attrib[key]
                xml = print_konstruktikon_xml(elem)
                sense.add_definition_xml(xml, lang=lang)

        le.add_sense(sense)
    return unicode(le)


def swefn(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    senses = entry.findall('Sense')
    single_features = ['BFNID', 'styledText', 'createdBy', 'entry_status']
    multiple_features = ['LU', 'compound', 'compoundExample', 'coreElement',
                         'domain', 'SweCxnID', 'problematicLU',
                         'suggestionForLU', 'inheritance', 'semanticType',
                         'comment', 'peripheralElement', 'BFNLUs',
                         'internal_comment']
    for sense_entry in senses:
        sense = jl.Sense(sense_entry.attrib.get('id', ''))
        jl.add_features(sense_entry, sense, single_features)
        for feat in multiple_features:
            jl.add_feature(sense_entry, sense, feat)

        # We currently ignore the role field of peripheralElements.
        # If they should be incuded again, use the code below
        # peripheral may have extra arguments in a feat
        # for feat in sense_entry.findall("feat"):
        #   #print(feat.get("att")):
        #   if feat.get("att")== 'peripheralElement':
        #       extra = ("role",feat.get("role")) if feat.get("role") else None
        #       sense.add_extrafeature(jl.FeatureExtra(feat.get("att"),
        #                                              feat.get("val"),extra=extra))

        # namespaces causes 'find' etc. to not work
        for elem in sense_entry:
            if elem.tag.split('}')[-1] == "example":
                xml = print_konstruktikon_xml(elem)
                sense.add_example_xml(xml)
            elif elem.tag.split('}')[-1] == "definition":
                xml = print_konstruktikon_xml(elem)
                sense.add_definition_xml(xml)
            elif elem.tag == "feat" and elem.attrib.get('att') == "definition":
                # old syntax in lmf, definition is a feat
                sense.add_definition_text(elem.attrib.get('val'))

        le.add_sense(sense)
    return unicode(le)


def print_konstruktikon_xml(xml):
    xml = etree.tostring(xml, encoding='utf-8')
    if type(xml) is bytes:  # konstruktikon has byte for some reason??
        xml = xml.decode('utf8')
    xml = xml.replace('\t', ' ')
    xml = xml.replace('"', '\\"')
    # xml = xml.replace("'", "\\'")
    xml = re.sub('xmlns:.*?=".*?"', '', xml)
    xml = re.sub('\n', '\\\\n', xml)
    return re.sub('<([^>]*?)([a-zA-Z0-9]*:.*?)', r'<\1', xml)


def saldo(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for form in entry.findall('.//FormRepresentation'):
        form_representation = jl.FormRepresentation()
        jl.add_feature(form, form_representation, 'baseform', 'writtenForm')
        jl.add_features(form, form_representation, ['partOfSpeech', 'lemgram',
                                                    'paradigm'])
        lemma.add_form_representation(form_representation)

    sense_entry = entry.find('Sense')
    sense = jl.Sense(sense_entry.attrib.get('id', ''))
    secondaries = []
    for rel in sense_entry.findall('SenseRelation'):
        for elem in list(rel):
            if elem.tag == "feat" and elem.attrib.get('val') == "primary":
                primary_relation = jl.SenseRelation(rel.attrib.get('targets'),
                                                    ['primary'])
                sense.add_sense_relation(primary_relation)
            if elem.tag == "feat" and elem.attrib.get('val') == "secondary":
                secondaries.append(rel.attrib.get('targets'))
    secondary_relation = jl.SenseRelation(secondaries, ['secondary'])
    sense.add_sense_relation(secondary_relation)
    primary = kids.get(sense_entry.attrib.get('id'), {}).get('primary', [])
    sense.add_sense_relation(jl.SenseRelation(primary, ["primary_children"]))
    seconds = kids.get(sense_entry.attrib.get('id'), {}).get('secondary', [])
    sense.add_sense_relation(jl.SenseRelation(seconds, ["secondary_children"]))

    le.add_sense(sense)
    return unicode(le)


def saldom(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for form in entry.findall('.//FormRepresentation'):
        form_representation = jl.FormRepresentation()
        jl.add_feature(form, form_representation, 'baseform', 'writtenForm')
        jl.add_features(form, form_representation, ['partOfSpeech', 'lemgram',
                                                    'paradigm', 'inherent'])
        lemma.add_form_representation(form_representation)

    # splitted mwe's are glued together again
    isopen = 0
    mwe_wfs = []
    for wf in entry.findall('.//WordForm'):
        wordform = jl.WordForm()
        for t in wf.findall('.//'):
            m = t.attrib.get('att')
            if m == 'msd':
                msd = t.attrib.get('val')
            if m == 'writtenForm':
                wf = t.attrib.get('val')
        mwe = re.search('.* (\d\d*):(\d\d*)-(\d\d*)', msd)
        msd = re.sub(' \d\d*:\d\d*-\d\d*$', '', msd)
        if mwe:
            if isopen >= int(mwe.group(2)):
                mwe_wfs.append(wf)
            else:
                isopen = int(mwe.group(3))
                mwe_wfs = [wf]
            if isopen == int(mwe.group(2)):
                wordform.add_feature(jl.Feature("index", mwe.group(1)))
                wordform.add_feature(jl.Feature("msd", msd))
                wordform.add_feature(jl.Feature("writtenForm", ' '.join(mwe_wfs)))
                le.add_wordform(wordform)
                mwe_wfs = []
                isopen = 0
        else:
            wordform.add_feature(jl.Feature("msd", msd))
            wordform.add_feature(jl.Feature("writtenForm", wf))
            le.add_wordform(wordform)

    return unicode(le)


def saldoe(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma

    sense_entry = entry.find('.//Sense')
    sense = jl.Sense(sense_entry.attrib.get('id', ''))
    for ex in sense_entry.findall('SenseExample'):
        sense_ex = jl.SenseExample(ex.find('.//feat[@att="text"]').
                                   attrib.get('val'))
        sense.add_sense_example(sense_ex)
    le.add_sense(sense)

    return unicode(le)


def lwt(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for form in entry.findall('.//FormRepresentation'):
        form_representation = jl.FormRepresentation()
        jl.add_feature(form, form_representation, 'baseform', 'writtenForm')
        # TODO is it ok with definition and example as simple feat here?
        jl.add_features(form, form_representation, ['definition', 'example',
                                                    'phonemic', 'gloss'])
        lang = [val for key, val in form.attrib.items()
                if key.split('}')[-1] == 'lang']
        if lang:
            form_representation.add_feature(jl.Feature('lang', lang[0]))
        lemma.add_form_representation(form_representation)

    sense_entry = entry.find('.//Sense')
    sense = jl.Sense(sense_entry.attrib.get('id', ''))
    for elem in list(sense_entry):
        if elem.tag == "feat" and elem.attrib.get('att')in ['saldoSense',
                                                            'lwtID', 'synset',
                                                            'type']:
            sense.add_feature(jl.Feature(elem.attrib.get('att'),
                                         elem.attrib.get('val')))
    le.add_saldoLinks(get_saldo_links(entry))
    le.add_sense(sense)
    return unicode(le)


def lexin(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    le.set_entrytype(entry.find('.//feat[@att="entryType"]').attrib.get('val'))
    lemma = jl.Lemma()
    le.lemma = lemma
    jl.add_features(entry, le, ['compareWith', 'see'])
    first_form = ''
    for form in entry.findall('.//FormRepresentation'):
        form_representation = jl.FormRepresentation()
        to_add = ['definition', 'example', 'lexinID', 'nativeOfSpeech',
                  'hyphenatedForm', 'mainWord', 'lexinVariant',
                  'partOfSpeech', 'phoneticForm', 'rank', 'rawForm', 'text']
        lang = [val for key, val in form.attrib.items()
                if key.split('}')[-1] == 'lang']
        if lang:
            form_representation.add_feature(jl.Feature('lang', lang[0]))
        jl.add_feature(form, form_representation, 'baseform', 'writtenForm')
        jl.add_features(form, form_representation, to_add)

        le.lemma.add_form_representation(form_representation)
        if not first_form:
            first_form = (form_representation, form)

    sense_entry = entry.find('.//Sense')
    add_extra_def(sense_entry, first_form)
    sense = jl.Sense(sense_entry.attrib.get('id', ''))
    add_example_definition_feat(sense_entry, sense)

    exampleid = 1
    for ex in sense_entry.findall('SenseExample'):
        typ = ''
        texts = []
        for feat in list(ex):
            lang = [val for key, val in feat.attrib.items()
                    if key.split('}')[-1] == 'lang']
            if feat.tag == 'feat' and feat.attrib.get('att') == 'text':
                text = feat.attrib.get('val')
                texts.append((text, lang))
            if feat.tag == 'feat' and feat.attrib.get('att') == 'type':
                typ = feat.attrib.get('val')

        # add one SenseExample per language
        for ex, lang in texts:
            # only allow one language per example
            lang = lang[0] if lang else ''
            sense_ex = jl.SenseExample(ex, _type=typ, _id=exampleid, lang=lang)
            sense.add_sense_example(sense_ex)

        exampleid += 1
    jl.add_features(sense_entry, sense, ['gram', 'lexinTheme', 'lexinID',
                                         'lexinLexemeNumber', 'lexinVariantID',
                                         'antonym', 'comment', 'compareWith',
                                         'desc', 'lexinVariant', 'usg'])
    le.add_sense(sense)

    for wf in entry.findall('.//WordForm'):
        wordform = jl.WordForm()
        jl.add_features(wf, wordform, ['lexinSpec', 'writtenForm', 'msd',
                                       'lexinMsd'])
        le.add_wordform(wordform)

    le.add_saldoLinks(get_saldo_links(entry))
    return unicode(le)


def add_example_definition_feat(sense_entry, sense):
    for elem in list(sense_entry):
        if elem.tag == "feat" and elem.attrib.get('att') == "definition":
            sense.add_definition_text(elem.attrib.get('val'))
        elif elem.tag.split('}')[-1] == "example":
                xml = print_konstruktikon_xml(elem)
                sense.add_example_xml(xml)


def add_extra_def(sense_entry, first_form):
    form_obj, form_entry = first_form
    f_deftext = form_entry.find("./feat[@att='text']")
    s_deftext = sense_entry.find("./feat[@att='definition']")
    if f_deftext is None and s_deftext is not None:
        form_obj.add_feature(jl.Feature('text',
                             s_deftext.attrib.get('val')))


def get_saldo_links(entry):
    links = jl.SaldoLinks()
    for elem in list(entry):
        if elem.tag.split('}')[-1] == "saldoLink":
            links.add(elem.attrib.get('ref'))
    return links


def dalin(entry, name, order, kids={}):
    # Sense.lbl, syn i lmf
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    xmlelem = list(entry.find('./xml'))[0]
    # TODO remove later, keep for valdation? Where to put it in the lmf?
    xml = etree.tostring(xmlelem, encoding='unicode')
    le.xml = xml.replace('\n', '')
    for rel in entry.findall('.//RelatedForm'):
        if rel.tag == "feat":
            le.add_relatedform(jl.RelatedForm(rel.attrib.get('att')),
                               jl.RelatedForm(rel.attrib.get('val')))
    fr = jl.FormRepresentation()
    form = entry.find('./Lemma/FormRepresentation')
    jl.add_feature(form, fr, 'baseform', 'writtenForm')
    jl.add_features(form, fr, ['lemgram', 'gram', 'usg', 'phoneticForm', 'hom',
                               'cmpd', 'hwtext', 'etym', 'partOfSpeech'])
    lemma.add_form_representation(fr)

    for wf in entry.findall('.//WordForm'):
        wordform = jl.WordForm()
        jl.add_features(wf, wordform, ['type', 'tag', 'msd', 'writtenForm'])
        le.add_wordform(wordform)

    for lmfsense in entry.findall('Sense'):
        sense = jl.Sense(lmfsense.attrib.get('id'), allow_many_defs=True)
        for elem in list(lmfsense):
            if elem.tag == "feat" and elem.attrib.get('att') == "definition":
                sense.add_definition_text(elem.attrib.get('val'))
        jl.add_features(lmfsense, sense, ['usg', 'note', 'lbl'])
        relations = {}
        for rel in lmfsense.findall('SenseRelation'):
            reltarget = rel.attrib.get('targets')
            for elem in list(rel):
                # the label was called 'type' in the old lmf version, but was
                # renamed in order to make the lexica consistent
                if elem.attrib.get('att') == 'label':
                    label = elem.attrib.get('val')
                    if label not in relations:
                        relations[label] = []
                    relations[label].append(reltarget)
        for lab, targets in relations.items():
            relation = jl.SenseRelation(targets, [lab])
            sense.add_sense_relation(relation)

        for ex in lmfsense.findall('SenseExample'):
            # exclude examples with no text
            if ex.find('.//feat[@att="text"]'):
                t_elem = ex.find('.//feat[@att="type"]')
                _type = t_elem.attrib.get('val') if t_elem else ''
                sense_ex = jl.SenseExample(ex.find('.//feat[@att="text"]').
                                           attrib.get('val'), _type=_type)
                sense.add_sense_example(sense_ex)

        le.add_sense(sense)
    return unicode(le)


def dalinbase(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for form in entry.findall('./Lemma/FormRepresentation'):
        fr = jl.FormRepresentation()
        jl.add_features(form, fr, ['partOfSpeech', 'lemgram', 'oldSpelling',
                                   'newSpelling', 'xref', 'paradigm'])
        lemma.add_form_representation(fr)

    return unicode(le)


def diapivot(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for form in entry.findall('./Lemma/FormRepresentation'):
        fr = jl.FormRepresentation()
        jl.add_features(form, fr, ['category', 'lemgram', "match"])
        lemma.add_form_representation(fr)
    return unicode(le)


def schlyter(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    xmlelem = list(entry.find('./xml'))[0]
    # TODO remove later, keep for valdation? Where to put it in the lmf?
    xml = etree.tostring(xmlelem, encoding='unicode')
    le.xml = xml.replace('\n', '')
    for form in entry.findall('./Lemma/FormRepresentation'):
        fr = jl.FormRepresentation()
        jl.add_features(form, fr, ['partOfSpeech', 'lemgram', 'information',
                                   'hwtext', 'gram', 'variant'])
        jl.add_feature(form, fr, 'baseform', 'writtenForm')
        lemma.add_form_representation(fr)

    for wf in entry.findall('.//WordForm'):
        wordform = jl.WordForm()
        jl.add_features(wf, wordform, ['msd', 'writtenForm'])
        le.add_wordform(wordform)

    for lmfsense in entry.findall('Sense'):
        sense = jl.Sense(lmfsense.attrib.get('id'), allow_many_defs=True)
        for elem in list(lmfsense):
            if elem.tag == "feat" and elem.attrib.get('att') == "definition":
                sense.add_definition_text(elem.attrib.get('val'))
        jl.add_features(lmfsense, sense, ['gram', 'text', 'V?U0A00', 'V?IPA**',
                                          'V?ISA**'])
        le.add_sense(sense)

    return unicode(le)


def soederwall(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    xmlelem = list(entry.find('./xml'))[0]
    # TODO remove later, keep for valdation? Where to put it in the lmf?
    xml = etree.tostring(xmlelem, encoding='unicode')
    le.xml = xml.replace('\n', '')
    for form in entry.findall('./Lemma/FormRepresentation'):
        fr = jl.FormRepresentation()
        jl.add_features(form, fr, ['partOfSpeech', 'lemgram', 'information',
                                   'oldForm', 'gram'])
        jl.add_feature(form, fr, 'baseform', 'writtenForm')
        lemma.add_form_representation(fr)

    for wf in entry.findall('.//WordForm'):
        wordform = jl.WordForm()
        jl.add_features(wf, wordform, ['msd', 'writtenForm', 'tag'])
        le.add_wordform(wordform)

    for lmfsense in entry.findall('Sense'):
        sense = jl.Sense(lmfsense.attrib.get('id'), allow_many_defs=True)
        for elem in list(lmfsense):
            if elem.tag == "feat" and elem.attrib.get('att') == "definition":
                sense.add_definition_text(elem.attrib.get('val'))
        jl.add_features(lmfsense, sense, ['writtenForm', 'gram', 'text',
                                          'AF0USNI', 'V0IPA**', 'V0ISA**'])
        le.add_sense(sense)

    return unicode(le)


def soederwallsupp(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    xmlelem = list(entry.find('./xml'))[0]
    # TODO remove later, keep for valdation? Where to put it in the lmf?
    xml = etree.tostring(xmlelem, encoding='unicode')
    le.xml = xml.replace('\n', '')
    for form in entry.findall('./Lemma/FormRepresentation'):
        fr = jl.FormRepresentation()
        jl.add_features(form, fr, ['partOfSpeech', 'lemgram', 'information',
                                   'gram'])
        jl.add_feature(form, fr, 'baseform', 'writtenForm')
        lemma.add_form_representation(fr)

    for wf in entry.findall('.//WordForm'):
        wordform = jl.WordForm()
        jl.add_features(wf, wordform, ['msd', 'writtenForm', 'tag'])
        le.add_wordform(wordform)

    for lmfsense in entry.findall('Sense'):
        sense = jl.Sense(lmfsense.attrib.get('id'), allow_many_defs=True)
        for elem in list(lmfsense):
            if elem.tag == "feat" and elem.attrib.get('att') == "definition":
                sense.add_definition_text(elem.attrib.get('val'))
        jl.add_features(lmfsense, sense, ['writtenForm', 'gram', 'text',
                                          'AF0USNI'])
        le.add_sense(sense)

    return unicode(le)


def swedberg(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for form in entry.findall('./Lemma/FormRepresentation'):
        fr = jl.FormRepresentation()
        jl.add_feature(form, fr, 'baseform', 'writtenForm')
        jl.add_features(form, fr, ['german', 'reference', 'danish', 'french',
                                   'partOfSpeech', 'variant', 'latinPhrase',
                                   'text', 'footnote', 'latin', 'greek',
                                   'syn', 'latinUncertain', 'lemgram',
                                   'information', 'gram'])
        lemma.add_form_representation(fr)

    for lmfsense in entry.findall('Sense'):
        sense = jl.Sense(lmfsense.attrib.get('id'), allow_many_defs=True)
        for elem in list(lmfsense):
            if elem.tag == "feat" and elem.attrib.get('att') == "definition":
                sense.add_definition_text(elem.attrib.get('val'))
        jl.add_features(lmfsense, sense, ['writtenForm', 'gram', 'text',
                                          'AF0USNI'])
        le.add_sense(sense)

        for ex in lmfsense.findall('SenseExample'):
            text = ''
            if ex.find('.//feat[@att="text"]') is not None:
                text = ex.find('.//feat[@att="text"]').attrib.get('val')
            sense_ex = jl.SenseExample(text)
            for lat in ex.findall('.//feat[@att="latinPhrase"]'):
                sense_ex.add_feat(jl.Feature("latinPhrase",
                                             lat.attrib.get('val')))
            sense.add_sense_example(sense_ex)

    return unicode(le)


def hellqvist(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    single_topfeatures = ['lastmodified', 'lastmodifiedBy']
    jl.add_features(entry, le, single_topfeatures)

    fr = jl.FormRepresentation()
    forms = entry.findall('./Lemma/FormRepresentation')
    for form in forms:
        lemma.add_form_representation(fr)
        jl.add_feature(form, fr, "baseform", fromname='writtenForm')
        jl.add_features(form, fr, ['lemgram', 'partOfSpeech'])

    for sense_entry in entry.findall('Sense'):
        sense = jl.Sense(entry.find('Sense').get('id', ''))
        # do not translate 'etym', it is duplicated in styledText
        jl.add_features(sense_entry, sense, ['styledText', 'hellqvistStatus',
                                             'see', 'sourceLanguage',
                                             'faksimilID'])
        le.add_sense(sense)

    for etym in entry.findall('etymology'):
        etym_obj = jl.Etymology()
        for etymon in etym.findall('etymon'):
            etymon_obj = etym_obj.add_etymon()
            for form in etymon.findall('form'):
                orth = form.find('orth')
                lang = 11
                for key, val in orth.attrib.items():
                    if key.split('}')[-1] == 'lang':
                        lang = val
                orth = form.find('orth').text or ''
                desc = form.find('note')
                desc = desc.text if desc is not None else ''
                etymon_obj.add_form(lang, orth, desc)
        le.add_etymology(etym_obj)

    return unicode(le)


def kelly(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    form = entry.find('./Lemma/FormRepresentation')
    fr = jl.FormRepresentation()
    lemma.add_form_representation(fr)
    jl.add_feature(form, fr, "baseform", fromname='writtenForm')
    jl.add_features(form, fr, ['formInformation', 'partOfSpeech',
                               'kellyPartOfSpeech', 'gram', 'kellyID', 'raw',
                               'wpm', 'cefr', 'source', 'grammar', 'example',
                               'rawFreq'])

    sense = jl.Sense(entry.find('Sense').get('id'))
    le.add_sense(sense)
    le.add_saldoLinks(get_saldo_links(entry))
    return unicode(le)


def parole(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    form = entry.find('./Lemma/FormRepresentation')
    fr = jl.FormRepresentation()
    lemma.add_form_representation(fr)
    jl.add_feature(form, fr, "baseform", fromname='writtenForm')
    jl.add_features(form, fr, ['partOfSpeech', 'valency', 'paroleID'])
    lmfsense = entry.find('Sense')
    sense = jl.Sense(lmfsense.get('id'))
    le.add_sense(sense)
    le.add_saldoLinks(get_saldo_links(entry))
    jl.add_feature(lmfsense, sense, 'saldoSense')

    return unicode(le)


def simple(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    form = entry.find('./Lemma/FormRepresentation')
    fr = jl.FormRepresentation()
    lemma.add_form_representation(fr)
    jl.add_feature(form, fr, "baseform", fromname='writtenForm')
    jl.add_features(form, fr, ['partOfSpeech', 'paroleID'])
    lmfsense = entry.find('Sense')
    sense = jl.Sense(lmfsense.get('id'))
    le.add_sense(sense)
    le.add_saldoLinks(get_saldo_links(entry))
    jl.add_feature(lmfsense, sense, 'saldoSense')
    feats_to_add = ['semanticType', 'domain', 'simpleSenseNumber', 'GLDB',
                    'GLDBExample', 'basicConcept', 'numberOfArguments',
                    'numberOfUsynSemuLinks', 'argumentRealisation',
                    'predicate', 'verbalizedNounType']
    jl.add_features(lmfsense, sense, feats_to_add)
    jl.add_feature(lmfsense, sense, "class")

    return unicode(le)


def swesaurus(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    for lmfsense in entry.findall('Sense'):
        sense = jl.Sense(lmfsense.get('id'))
        sense_relation = jl.SwesaurusRelations()
        le.add_sense(sense)

        for rel in lmfsense.findall('SenseRelation'):
            reltarget = rel.attrib.get('targets')
            relations = []
            for elem in list(rel):
                att, val = elem.attrib.get('att'), elem.attrib.get('val')
                relations.append((att, val))
            sense_relation.add_relations(reltarget, relations)
    sense.add_swesaurusrelation(sense_relation)

    #   for rel in lmfsense.findall('SenseRelation'):
    #       reltarget = rel.attrib.get('targets')
    #       relations = {}
    #       for elem in list(rel):
    #           if elem.attrib.get('att') == 'label':
    #               label = elem.attrib.get('val')
    #               if label not in relations:
    #                   relations[label] = []
    #               relations[label].append(reltarget)
    #   for lab, targets in relations.items():
    #       relation = jl.SenseRelation(targets, [lab])
    #       sense.add_sense_relation(relation)
    return unicode(le)

# gammal syntax: "SenseRelations":
#                            {
#                                "syn":
#                                [
#                                     "gratifikation..1"
#                                ]
#
# ny syntax: "SenseRelations":
#                            [
#                                {
#                                    "targets": "kostnad..1",
#                                    "source": "fsl",
#                                    "degree": "64",
#                                    "label": "syn"
#                                },
#
#        <SenseRelation targets="kulram..1">
#          <feat att="label" val="syn" />
#          <feat att="degree" val="86" />
#          <feat att="source" val="fsl" />
#        </SenseRelation>
#        <SenseRelation targets="kulram..1">
#          <feat att="label" val="syn" />
#          <feat att="degree" val="100" />
#          <feat att="source" val="wiktionary" />
#        </SenseRelation>


def termswefin(entry, name, order, kids={}):
    import termswefinlib as termjl
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    single_topfeatures = ['lastmodified', 'lastmodifiedBy', 'termstatus',
                          'terminternalcomment']
    for subtype in jl.findfeatlist(entry, 'entryType'):
        le.add_feature(jl.Feature('subtype', subtype, forcelist=True))
    jl.add_features(entry, le, single_topfeatures)
    langobjs = {}
    targets = termjl.Targetlangs()
    lemma.add_object(targets)

    for form in entry.findall('.//FormRepresentation'):
        langtype = jl.findfeat(form, 'type')
        lang = ''
        for key, val in form.attrib.items():
            if key.endswith('lang'):
                lang = val
        lang_code = lang_encode(lang)
        if lang not in langobjs:
          langobjs[lang] = {"lang_code": lang_code, "langtype": langtype,
                            "compound": [], "forms": []}
        if langtype == "source":
            defin =  jl.findfeat(form, 'definition')
            if defin:
                langobjs[lang]['definition'] = defin
        example = jl.findfeat(form, 'example')
        if example:
            langobjs[lang]['example'] = example
        source = jl.findfeat(form, 'source')
        if source:
            langobjs[lang]['source'] = source

        comment = jl.findfeat(form, 'comment')
        wf = jl.findfeat(form, 'writtenForm')
        if comment or wf:
            langobjs[lang]['forms'].append((wf, comment))

    for lang, feats in langobjs.items():
        if feats['langtype'] == "source":
            baseobj = termjl.Baselang(feats['lang_code'])
            baseobj.definition = feats.get("definition", '')
            lemma.add_object(baseobj)
        elif feats['langtype'] == "target":
            baseobj = termjl.Targetlang(feats['lang_code'])
            targets.add_target(baseobj)

        for wf, comment in feats['forms']:
            baseobj.forms.append({"wordform": wf, "comment": comment})

        baseobj.example = feats.get("example", '')
        baseobj.source = feats.get("source", '')
        langobjs[lang] = baseobj

    sense = entry.find('Sense')
    for ex in sense.findall('SenseExample'):

        for feat in ex.findall("feat"):
            if feat.get("att") == 'text':
                extext = feat.get("val")
                for key, val in feat.attrib.items():
                    if key.endswith('lang'):
                        lang = val
                baseobj = langobjs[lang]
                baseobj.compound.append(extext)

    return unicode(le)


def wordnet(entry, name, order, kids={}):
    le = jl.LexicalEntry(name, order)
    lemma = jl.Lemma()
    le.lemma = lemma
    le.add_saldoLinks(get_saldo_links(entry))

    for form in entry.findall('.//FormRepresentation'):
        form_representation = jl.FormRepresentation()
        jl.add_features(form, form_representation, ['partOfSpeech',
                                                    'nativePartOfSpeech',
                                                    'gloss'])
        lemma.add_form_representation(form_representation)

    lmfsense = entry.find('Sense')
    sense = jl.Sense(lmfsense.get('id'))
    le.add_sense(sense)
    add_example_definition_feat(lmfsense, sense)
    feats_to_add = ['synset', 'type', 'core', 'frequency', 'example']
    jl.add_features(lmfsense, sense, feats_to_add)
    jl.add_feature(lmfsense, sense, 'saldoSense')

    return unicode(le)


# Help functions
def lang_encode(langcode):
    try:
        # If it already is a iso language code, return it
        return pycountry.languages.get(name=langcode).name
    except KeyError:
        pass
    try:
        # If it is a language name, return the iso code
        return pycountry.languages.get(alpha_3=langcode).name
    except KeyError:
        pass
    try:
        # Try lowercasing the name
        return pycountry.languages.get(alpha_3=langcode.lower()).name
    except KeyError:
        # Just return the input string
        return langcode


# For compatibility with python3 :(
def unicode(obj):
    return obj.__unicode__()

if __name__ == "__main__":
    lexicon = sys.stdin
    name = sys.argv[1]
    order = -1
    if len(sys.argv) > 2:
        lexicon = sys.argv[2]
    if len(sys.argv) > 3:
        order = sys.argv[3]
    print '['
    print ',\n'.join(get_lexicon(lexicon, name, order, return_bulk=True,
                                 make_bulk=False))
    print ']'
