import sys
sys.path.append('.')
import sb.converter.lmflib as xml
import sb.converter.xmldiff as xmldiff
import json
import re
import pycountry  # pip3 install pycountry
import sys
import xml.etree.ElementTree as etree


# Help functions
def lang_encode(language):
    try:
        # If it already is a iso language code, return it
        return pycountry.languages.get(alpha_3=language).alpha_3
    except KeyError:
        pass
    try:
        # If it is a language name, return the iso code
        return pycountry.languages.get(name=language).alpha_3
    except KeyError:
        pass
    try:
        # Try titelize the name
        return pycountry.languages.get(name=language.title()).alpha_3
    except KeyError:
        # Just return the input string
        return language


def force_list(obj, field):
    xs = obj.get(field, [])
    if type(xs) != list:
        return [xs]
    return xs


def add_features(obj, target, names):
    for name in names:
        add_feature(obj, target, name)


def add_feature(obj, target, name, fromname=''):
    if not fromname:
        fromname = name
    if obj.get(fromname):
        if type(obj[fromname]) == list:
            raise Exception('List in feature', str(obj), name)
        target.add_feature(xml.Feature(name, obj[fromname]))


def add_feature_list(obj, target, name):
    for toadd in force_list(obj, name):
        target.add_feature(xml.Feature(name, toadd))


# Lexicon translations
def saldo(obj, lmf):
    lexical_entry = xml.LexicalEntry()
    lemma = xml.Lemma()
    for form in obj.get('FormRepresentations', [{}]):
        form_representation = xml.FormRepresentation()
        add_feature(form, form_representation, 'writtenForm', 'baseform')
        add_features(form, form_representation, ['partOfSpeech', 'lemgram',
                                                 'paradigm'])
        lemma.add_form_representation(form_representation)

    sense_obj = obj['Sense'][0]
    lexical_entry.lemma = lemma
    sense = xml.Sense(sense_obj['senseid'])
    if sense_obj.get('SenseRelations', {}).get('primary'):
        primary_relation = xml.SenseRelation(sense_obj['SenseRelations']['primary'],
                                             ['primary'])
        sense.add_sense_relation(primary_relation)
    for sec in sense_obj.get('SenseRelations', {}).get('secondary', []):
        secondary_relation = xml.SenseRelation(sec, ['secondary'])
        sense.add_sense_relation(secondary_relation)

    lexical_entry.add_sense(sense)
    lmf.add_lexical_entry(lexical_entry)


def saldom(obj, lmf):
    lexical_entry = xml.LexicalEntry()
    lemma = xml.Lemma()
    form = obj['FormRepresentations'][0]
    form_representation = xml.FormRepresentation()
    add_feature(form, form_representation, 'writtenForm', 'baseform')
    add_features(form, form_representation, ['lemgram', 'partOfSpeech',
                                             'paradigm'])
    add_feature_list(form, form_representation, 'inherent')
    lemma.add_form_representation(form_representation)
    lexical_entry.lemma = lemma
    for wf in obj['WordForms']:
        wordform = xml.WordForm()
        add_feature(wf, wordform, "writtenForm")
        add_feature(wf, wordform, "msd")
        lexical_entry.add_wordform(wordform)
        # lexical_entry.add_sense(wf)
    lmf.add_lexical_entry(lexical_entry)


# Saldo example:
def saldoe(obj, lmf):
    le = xml.LexicalEntry()
    le.lemma = xml.Lemma()
    saldo = obj['Sense'][0]['senseid']
    lmf._le_senses.add((saldo, le))
    sense = xml.Sense(saldo)
    le.add_sense(sense)
    sense = le.senses[0]
    for ex in obj['Sense'][0]['SenseExamples']:
        sense.add_sense_example(xml.SenseExample(ex['text']))

    lmf.add_lexical_entry(le)


def sentimentlex(obj, lmf):
    lexical_entry = xml.LexicalEntry()
    lemma = xml.Lemma()
    form = obj['FormRepresentations'][0]
    form_representation = xml.FormRepresentation()
    add_features(form, form_representation, ['partOfSpeech', 'lemgram'])
    for wf in force_list(form, 'baseform'):  # may be more than one baseform
        form_representation.add_feature(xml.Feature("writtenForm", wf))
    if 'lemgramFrequency' in form:
        add_feature(form, form_representation, 'lemgramFrequency')
    if 'lemmaFrequency' in form:
        add_feature(form, form_representation, 'lemmaFrequency')
    lemma.add_form_representation(form_representation)

    sense_obj = obj['Sense'][0]
    lexical_entry.lemma = lemma
    sense = xml.Sense(sense_obj['senseid'])
    if sense_obj['SenseExamples'][0].get('text'):
        example = xml.SenseExample(sense_obj['SenseExamples'][0]['text'],
                                   _type="text")
        sense.add_sense_example(example)
    if sense_obj['SenseExamples'][0].get('lemgrams'):
        example = xml.SenseExample(sense_obj['SenseExamples'][0]['lemgrams'],
                                   _type="lemgrams")
        sense.add_sense_example(example)

    semantic_label = xml.SemanticLabel([
        ("polarity", sense_obj["polarity"]),
        ("strength", sense_obj["strength"]),
        ("confidence", sense_obj["confidence"])
    ], _type="sentiment")
    sense.add_semantic_label(semantic_label)

    lexical_entry.add_sense(sense)
    lmf.add_lexical_entry(lexical_entry)


def dalinm(obj, lmf):
    saldom(obj, lmf)


# swesaurus:
def swesaurus(obj, lmf):
    le = xml.LexicalEntry()
    le.lemma = xml.Lemma()
    saldo1 = obj['Sense'][0]['senseid']
    saldo1 = saldo1.strip()
    lmf._le_senses.add((saldo1, le))
    lmf.add_lexical_entry(le)
    sense = xml.Sense(saldo1)
    le.add_sense(sense)

    for sense_obj in obj['Sense']:
        for relation in sense_obj['SenseRelations']:
            saldo2 = relation['targets'].strip()

            sense_relation = xml.SenseRelation(saldo2, [relation['label']])
            add_features(relation, sense_relation, ['degree', 'source'])
            sense.add_sense_relation(sense_relation)


# lwt, ok:
def lwt(obj, lmf):
    lmf.useNamespace = True
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        form_representation = xml.FormRepresentation()
        baseform = force_list(form, 'baseform')
        for wf in baseform:
            form_representation.add_feature(xml.Feature("writtenForm", wf))
            # example and definition in FormRepresentation will look different
            # than in Sense
        add_features(form, form_representation, ['definition', 'example',
                                                 'phonemic', 'gloss'])
        form_representation.add_attrib(xml.Attribute('xml:lang', form['lang']))
        lemma.add_form_representation(form_representation)

    sense_obj = obj['Sense'][0]
    sense = xml.Sense(sense_obj['senseid'])
    le.add_sense(sense)
    for s in force_list(sense_obj, 'saldoSense'):
        sense.add_feature(xml.Feature("saldoSense", s))
    sense.add_feature(xml.Feature("lwtID", sense_obj['lwtID']))
    for s in force_list(sense_obj, 'synset'):
        sense.add_feature(xml.Feature("synset", s))
    for typ in force_list(sense_obj, "type"):
        sense.add_feature(xml.Feature("type", typ))

    for link in obj.get('saldoLinks', []):
        le.add_saldoLink(xml.SaldoLink(link))
    lmf.add_lexical_entry(le)


def lexin(obj, lmf):
    lmf.useNamespace = True

    le = xml.LexicalEntry()
    le.lemma = xml.Lemma()

    le.add_feature(xml.Feature('entryType', obj.get('entryType')))
    add_features(obj, le, ['compareWith', 'see'])
    for form in obj['FormRepresentations']:
        form_representation = xml.FormRepresentation()
        to_add = ['definition', 'example', 'lexinID', 'nativeOfSpeech',
                  'hyphenatedForm', 'mainWord', 'lexinVariant',
                  'partOfSpeech', 'phoneticForm', 'rank', 'rawForm', 'text']

        form_representation.add_attrib(xml.Attribute('xml:lang', form['lang']))
        for toadd in force_list(form, 'baseform'):
            form_representation.add_feature(xml.Feature('writtenForm', toadd))
        add_features(form, form_representation, to_add)

        le.lemma.add_form_representation(form_representation)

    sense_obj = obj['Sense'][0]
    sense = xml.Sense(sense_obj['senseid'])

    examples = {}
    for ex in sense_obj.get('SenseExamples', []):
        lang = ex.get('lang', '')
        text = ex.get('text', '')
        typ = ex.get('type', '')
        _id = ex.get('example_id')
        if _id not in examples:
            examples[_id] = []
        examples[_id].append((lang, text, typ))
    for _id, ex in examples.items():
        typ = ex[0][-1]
        sense_ex = xml.SenseExample(_type=typ)
        for lang, text, typ in ex:
            sense_ex.add_example(example=text, lang=lang)
        sense.add_sense_example(sense_ex)

    deftext = sense_obj.get('definition', {})
    if 'text' in deftext:
        sense.add_feature(xml.Feature("definition", deftext['text']))

    add_features(sense_obj, sense, ['lexinID', 'lexinLexemeNumber',
                                    'lexinVariantID', 'lexinVariant',
                                    'desc'])

    add_feature_list(sense_obj, sense, 'lexinTheme')
    add_feature_list(sense_obj, sense, 'comment')
    add_feature_list(sense_obj, sense, 'gram')
    add_feature_list(sense_obj, sense, 'antonym')
    add_feature_list(sense_obj, sense, 'compareWith')
    add_feature_list(sense_obj, sense, 'usg')
    le.add_sense(sense)

    for wf in obj.get('WordForms', []):
        wordform = xml.WordForm()
        add_features(wf, wordform, ['writtenForm', 'msd', 'lexinMsd',
                                    'lexinSpec'])
        le.add_wordform(wordform)

    for link in obj.get('saldoLinks', []):
        le.add_saldoLink(xml.SaldoLink(link))
    lmf.add_lexical_entry(le)


def parole(obj, lmf):
    lmf.useNamespace = True
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    fr = xml.FormRepresentation()
    form = obj['FormRepresentations'][0]
    sense = obj['Sense'][0]
    lemma.add_form_representation(fr)
    s = xml.Sense(sense['senseid'])
    le.add_sense(s)
    add_features(form, fr, ['partOfSpeech', 'valency', 'paroleID'])
    fr.add_feature(xml.Feature("writtenForm", form['baseform']))
    for sid in force_list(sense, 'saldoSense'):
        le.add_saldoLink(xml.SaldoLink(sid))
        s.add_feature(xml.Feature("saldoSense", sid))
    lmf.add_lexical_entry(le)


# simple:
def simple(obj, lmf):
    lmf.useNamespace = True
    le = xml.LexicalEntry()
    obj_sense = obj['Sense'][0]
    sense = xml.Sense(obj_sense['senseid'])
    le.add_sense(sense)

    feats_to_add = ['semanticType', 'domain', 'simpleSenseNumber', 'GLDB',
                    'GLDBExample', 'basicConcept', 'numberOfArguments',
                    'numberOfUsynSemuLinks', 'argumentRealisation',
                    'predicate', 'verbalizedNounType']
    add_features(obj_sense, sense, feats_to_add)

    for c in force_list(obj_sense, 'class'):
        sense.add_feature(xml.Feature("class", c))

    lemma = xml.Lemma()
    le.lemma = lemma
    fr = xml.FormRepresentation()
    form = obj['FormRepresentations'][0]
    lemma.add_form_representation(fr)
    fr.add_feature(xml.Feature("partOfSpeech", form['partOfSpeech']))
    fr.add_feature(xml.Feature("writtenForm", form['baseform']))
    fr.add_feature(xml.Feature("paroleID", form['paroleID']))
    for s in force_list(obj_sense, 'saldoSense'):
        le.add_saldoLink(xml.SaldoLink(s))
        sense.add_feature(xml.Feature("saldoSense", s))
    lmf.add_lexical_entry(le)


def kelly(obj, lmf):
    lmf.useNamespace = True
    sense_obj, form = obj['Sense'][0], obj['FormRepresentations'][0]
    le = xml.LexicalEntry()
    sense = xml.Sense(sense_obj['senseid'])
    le.add_sense(sense)
    for s in obj.get('saldoLinks', []):
        le.add_saldoLink(xml.SaldoLink(s))
        sense.add_feature(xml.Feature("saldoSense", s))

    lemma = xml.Lemma()
    le.lemma = lemma
    form_representation = xml.FormRepresentation()
    lemma.add_form_representation(form_representation)
    form_representation.add_feature(xml.Feature("writtenForm",
                                                form['baseform']))
    feats_to_add = ['formInformation', 'partOfSpeech', 'kellyPartOfSpeech',
                    'gram', 'kellyID', 'raw', 'wpm', 'cefr', 'source',
                    'grammar', 'example', 'rawFreq']
    add_features(form, form_representation, feats_to_add)
    lmf.add_lexical_entry(le)


def wordnet(obj, lmf):
    lmf.useNamespace = True
    le = xml.LexicalEntry()
    sense = xml.Sense(obj['Sense'][0]['senseid'])
    for link in obj['saldoLinks']:
        le.add_saldoLink(xml.SaldoLink(link))
    lemma = xml.Lemma()
    le.lemma = lemma
    form = obj['FormRepresentations'][0]
    fr = xml.FormRepresentation()
    add_feature_list(form, fr, 'gloss')
    add_feature(form, fr, "partOfSpeech")
    add_feature(form, fr, "nativePartOfSpeech")

    le.add_sense(sense)
    sense_obj = obj['Sense'][0]
    sense.add_feature(xml.Feature("definition",
                      sense_obj['definition']['text']))

    add_features(sense_obj, sense, ['synset', 'type', 'core', 'frequency',
                                    'saldoSense'])
    add_feature_list(sense_obj, sense, 'example')
    lemma.add_form_representation(fr)
    lmf.add_lexical_entry(le)


# Diapivot:
def diapivot(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        fr.add_feature(xml.Feature("category", form['category']))
        fr.add_feature(xml.Feature("lemgram", form['lemgram']))
        if form.get('match'):
            fr.add_feature(xml.Feature("match", form['match']))
        lemma.add_form_representation(fr)
    lmf.add_lexical_entry(le)


def dalinbase(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        add_features(form, fr, ['lemgram', 'oldSpelling', 'newSpelling',
                                'xref', 'partOfSpeech', 'paradigm'])
        lemma.add_form_representation(fr)
    lmf.add_lexical_entry(le)


def dalin(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    le.xml = obj['xml']  # remove later, keep for validation?
    if 'RelatedForm' in obj:
        rel = obj['RelatedForm']
        label = list(rel.keys())[0]
        le.add_relatedform(xml.RelatedForm(obj['RelatedForm'][label]))
    fr = xml.FormRepresentation()
    form = obj['FormRepresentations'][0]
    if form.get('baseform'):
        fr.add_feature(xml.Feature("writtenForm", form['baseform']))
    add_features(form, fr, ['lemgram', 'partOfSpeech'])
    add_feature_list(form, fr, 'usg')
    add_feature_list(form, fr, 'phoneticForm')
    add_feature_list(form, fr, 'gram')
    add_feature_list(form, fr, 'cmpd')
    add_feature_list(form, fr, 'hwtext')
    add_feature_list(form, fr, 'etym')
    add_feature_list(form, fr, 'hom')
    lemma.add_form_representation(fr)

    wflist = obj.get('WordForms', [])
    for wf in wflist:
        wordform = xml.WordForm()
        # there is one wordform without writtenform
        if 'writtenForm' in wf:
            wordform.add_feature(xml.Feature("writtenForm", wf['writtenForm']))
        if 'msd' in wf:
            wordform.add_feature(xml.Feature("msd", wf['msd']))
        if 'type' in wf:
            wordform.add_feature(xml.Feature("type", wf['type']))
        if 'tag' in wf:
            wordform.add_feature(xml.Feature("tag", wf['tag']))
        if 'text' in wf:
            wordform.add_feature(xml.Feature("text", wf['text']))
        le.add_wordform(wordform)

    senses = obj.get('Sense', [])
    for sense_obj in senses:
        # sense examples from old xml have no id
        sense = xml.Sense(sense_obj.get('senseid', ''))
        add_feature_list(sense_obj, sense, 'usg')
        add_feature_list(sense_obj, sense, 'note')

        deftext = sense_obj.get('definition', {})
        for text in force_list(deftext, 'text'):
            sense.add_feature(xml.Feature("definition", text))

        for relation, targets in sense_obj.get('SenseRelations', {}).items():
            for target in targets:
                sense.add_sense_relation(xml.SenseRelation(target, [relation]))

        for example in sense_obj.get('SenseExamples', []):
            exs = force_list(example, 'text')
            tag = example.get('tag', '')
            _type = example.get('type', '')
            sense_ex = xml.SenseExample(exs[0], tag, _type)
            for ex in exs[1:]:
                sense_ex.add_example(ex)
            sense.add_sense_example(sense_ex)

        add_feature_list(sense_obj, sense, 'lbl')

        le.add_sense(sense)
    lmf.add_lexical_entry(le)


def swedberg(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        add_features(form, fr, ['danish', 'syn'])
        add_features(form, fr, ['lemgram', 'usg'])
        add_feature(form, fr, 'writtenForm', 'baseform')
        add_feature_list(form, fr, 'partOfSpeech')
        add_feature_list(form, fr, 'french')
        add_feature_list(form, fr, 'german')
        add_feature_list(form, fr, 'greek')
        add_feature_list(form, fr, 'latin')
        add_feature_list(form, fr, 'latinPhrase')
        add_feature_list(form, fr, 'latinUncertain')
        add_feature_list(form, fr, 'reference')
        add_feature_list(form, fr, 'variant')
        add_feature_list(form, fr, 'text')
        add_feature_list(form, fr, 'gram')
        add_feature_list(form, fr, 'footnote')
        le.lemma.add_form_representation(fr)

    for sense_obj in obj['Sense']:
        sense = xml.Sense(sense_obj.get('senseid'))
        for ex in sense_obj.get('SenseExamples', []):
            sense_ex = xml.SenseExample(ex['text'])
            sense.add_sense_example(sense_ex)
            for lat in force_list(ex, 'latinPhrase'):
                sense_ex.add_feature(xml.Feature('latinPhrase', lat))
        le.add_sense(sense)

    lmf.add_lexical_entry(le)


def swedbergm(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        fr.add_feature(xml.Feature("lemgram", form['lemgram']))
        fr.add_feature(xml.Feature("writtenForm", form['baseform']))
        fr.add_feature(xml.Feature("paradigm", form["paradigm"]))
        if form.get('partOfSpeech'):
            fr.add_feature(xml.Feature("partOfSpeech", form['partOfSpeech']))
        le.lemma.add_form_representation(fr)
    wflist = obj.get('WordForms', [])
    for wf in wflist:
        wordform = xml.WordForm()
        wordform.add_feature(xml.Feature("writtenForm", wf['writtenForm']))
        wordform.add_feature(xml.Feature("msd", wf['msd']))
        le.add_wordform(wordform)
    lmf.add_lexical_entry(le)


def fsvm(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        fr.add_feature(xml.Feature("writtenForm", form['baseform']))
        add_features(form, fr, ["lemgram", "inherent", "paradigm",
                                "partOfSpeech"])
        le.lemma.add_form_representation(fr)
    wflist = obj.get('WordForms', [])
    for wf in wflist:
        wordform = xml.WordForm()
        add_features(wf, wordform, ["writtenForm", "msd"])
        le.add_wordform(wordform)
    lmf.add_lexical_entry(le)


def ao(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    fr = xml.FormRepresentation()
    form = obj['FormRepresentations'][0]
    fr.add_feature(xml.Feature("writtenForm", form['baseform']))
    for l in force_list(form, 'lemgram'):
        fr.add_feature(xml.Feature("lemgram", l.strip()))
    fr.add_feature(xml.Feature("partOfSpeech", form['partOfSpeech']))
    fr.add_feature(xml.Feature("nativePartOfSpeech", form['nativePartOfSpeech']))
    fr.add_feature(xml.Feature("rank", form['rank']))
    le.lemma.add_form_representation(fr)
    sense = xml.Sense(obj['Sense'][0]['senseid'])
    le.add_sense(sense)
    lmf.add_lexical_entry(le)


def bliss(obj, lmf):
    lmf.namespaces = {'karp': "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp"}
    lmf.useNamespace = True
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    fr = xml.FormRepresentation()
    form = obj['FormRepresentations'][0]
    for l in force_list(form, 'gloss'):
        fr.add_feature(xml.Feature("gloss", l.strip()))
    add_features(form, fr, ['blissID', 'symbolType', 'BCI_AV'])
    le.lemma.add_form_representation(fr)

    if 'saldoLinks' in obj:
        for link in obj['saldoLinks']:
            if link:
                le.add_saldoLink(xml.SaldoLink(link))

    for c in obj.get('ListOfComponents', []):
        # le.add_component(xml.Component(c['Component']['entry']))
        le.add_component(xml.Component(c))

    # Sense ids are excluded, since they provide no new information
    # sense = xml.Sense(obj['Sense'][0]['senseid'])
    # le.add_sense(sense)

    add_features(obj, le, ['symbolWidth', 'symbolHeight', 'symbolCenter'])
    add_feature_list(obj, le, 'symbolPath')
    lmf.add_lexical_entry(le)


# TODO test this
def blingbring(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    fr = xml.FormRepresentation()
    form = obj['FormRepresentations'][0]
    fr.add_feature(xml.Feature("writtenForm", form['baseform']))
    fr.add_feature(xml.Feature("roget_head_id", form['roget']['id']))
    fr.add_feature(xml.Feature("bring_entry_id", form['bring']['id']))
    le.lemma.add_form_representation(fr)

    for senseobj in obj.get('Sense', []):
        sense = xml.Sense(senseobj['senseid'])
        le.add_sense(sense)

    lmf.add_lexical_entry(le)


def hellqvist(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    le.lemma = lemma
    single_topfeatures = ['lastmodified', 'lastmodifiedBy']
    add_features(obj, le, single_topfeatures)
    forms = obj['FormRepresentations']
    for form in forms:
        fr = xml.FormRepresentation()
        lemma.add_form_representation(fr)
        for wf in force_list(form, 'baseform'):  # may be more than one baseform
            fr.add_feature(xml.Feature("writtenForm", wf))
        add_features(form, fr, ['lemgram'])
        add_feature_list(form, fr, 'partOfSpeech')

    for sense_obj in obj['Sense']:
        sense = xml.Sense(obj['Sense'][0].get('senseid', ''))
        add_features(sense_obj, sense, ['styledText', 'hellqvistStatus',
                                        'faksimilID'])
        add_feature_list(sense_obj, sense, 'sourceLanguage')
        etym = re.sub('<.*?>', '', sense_obj['styledText'])
        sense.add_feature(xml.Feature("etym", etym))
        for see in force_list(sense_obj, 'see'):
            sense.add_feature(xml.Feature("see", see))
        le.add_sense(sense)

    etym_obj = obj.get('Etymology', {})
    if etym_obj:
        etym = xml.Etymology()
        for form in etym_obj.get('relations', []):
            etymon = etym.add_etymon()
            etymon.add_form(form.get('lang', ''), form.get('form', ''),
                            form.get('desc', ''))
        le.add_etymology(etym)

    lmf.add_lexical_entry(le)


def swefn(obj, lmf):
    lmf.namespaces = {'swefn': "http://spraakbanken.gu.se/swe/resurs/swefn",
                      'karp': "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp",
                      'konst': "http://spraakbanken.gu.se/swe/resurs/konstruktikon",
                      }
    lmf.useNamespace = True
    le = xml.LexicalEntry()
    le.set_lang("swe")
    lemma = xml.Lemma()
    le.lemma = lemma
    single_features = ['BFNID', 'styledText', 'createdBy', 'entry_status',
                       'createdDate']
    multiple_features = ['LU', 'compound', 'compoundExample', 'coreElement',
                         'domain', 'SweCxnID', 'problematicLU',
                         'suggestionForLU', 'inheritance', 'semanticType',
                         'comment', 'peripheralElement', 'BFNLUs',
                         'internal_comment']
    for sense_obj in obj['Sense']:
        sense = xml.Sense(sense_obj.get('senseid', ''))
        for ex in sense_obj.get('examples', []):
            if ex.get('xml', ''):
                sense.add_from_xml(ex['xml'])
        add_features(sense_obj, sense, single_features)
        for feat in multiple_features:
            add_feature_list(sense_obj, sense, feat)
        # We currently ignore the role field of peripheralElements.
        # If they should be incuded again, use the code below
        # for peri in sense_obj.get('peripheralElement', []):
        #     extra = ("role", peri.get("role")) if peri.get("role") else None
        #     sense.add_feature(xml.Feature('peripheralElement', peri['val'], extra=extra))
        le.add_sense(sense)
        sdef = sense_obj.get('definition', {}).get('xml')
        if sdef:
            sense.add_from_xml(sdef)
        sdef = sense_obj.get('definition', {}).get('text')
        if sdef:
            sense.add_definition_text(sdef)
    lmf.add_lexical_entry(le)


# TODO lägg till datum etc!
def konstruktikon(obj, lmf, namespaces='', lang='swe'):
    # extra_comment is not exported
    if not obj.get('Sense', ''):
        # print('bad object', obj, file=sys.stderr)
        return

    lmf.useNamespace = True
    if not namespaces:
        namespaces = {'karp': "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp",
                      'konst': "http://spraakbanken.gu.se/swe/resurs/konstruktikon"
                      }
    lmf.namespaces = namespaces

    # cxn_language only in multi_cxn
    if 'cxn_language' in obj:
        lang = obj['cxn_language']

    le = xml.LexicalEntry()
    le.set_lang(lang)
    lemma = xml.Lemma()
    le.lemma = lemma
    single_topfeatures = ['lastmodified', 'lastmodifiedBy']
    add_features(obj, le, single_topfeatures)

    sense_objs = obj['Sense']
    single_features = ['BCxnID', 'cat', 'comment', 'createdBy', 'entry_status',
                       'illustration', 'cefr']
    # reference is single for SweCxn but multiple for RusCxn
    multiple_features = ['coll', 'type', 'inheritance', 'cee', 'evokes',
                         'internal_comment', 'reference', 'other_examples',
                         'structure', 'sweccnLink']

    for sense_obj in sense_objs:
        sense = xml.Sense(sense_obj.get('senseid'))
        add_features(sense_obj, sense, single_features)
        for feat in multiple_features:
            add_feature_list(sense_obj, sense, feat)
        for intc in sense_obj.get('int_const_elem', []):
            # TODO make this work then do the same for ext
            sense.add_int_const_elem(xml.IntConstElem(intc))
        for extc in sense_obj.get('ext_const_elem', []):
            sense.add_ext_const_elem(xml.ExtConstElem(extc))
        for ex in sense_obj.get('examples', []):
            if type(ex) != dict:
                # print('old construction!')
                continue
            if ex.get('xml', ''):
                sense.add_from_xml(ex['xml'])
        for ex in sense_obj.get('definitions', []):  # to be removed
            sense.add_from_xml(ex)
        for deftype in ["definition", "definition_eng", "definition_nor"]:
            kdef = sense_obj.get(deftype, {}).get('xml')
            lang = deftype.split('_')[-1] if '_' in deftype else ''
            if kdef:
                sense.add_from_xml(kdef, lang=lang)
        le.add_sense(sense)
    lmf.add_lexical_entry(le)


def konstruktikonrus(obj, lmf):
    ns = {"rusfn": "http://spraakbanken.gu.se/swe/resurs/rusfn",
          "karp": "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp",
          "konst": "http://spraakbanken.gu.se/swe/resurs/konstruktikon"}
    konstruktikon(obj, lmf, namespaces=ns, lang='rus')


def schlyter(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    # xml: remove later, keep for validation? Where to put it in the lmf?
    le.xml = obj['xml']
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        add_features(form, fr, ['partOfSpeech', 'lemgram', 'information',
                                'hwtext', 'gram', 'variant'])
        add_feature(form, fr, 'writtenForm', 'baseform')
        le.lemma.add_form_representation(fr)

    for sense_obj in obj.get('Sense', []):
        sense = xml.Sense(sense_obj['senseid'])
        add_feature_list(sense_obj, sense, 'gram')
        add_features(sense_obj, sense, ['text', 'V?U0A00', 'V?IPA**', 'V?ISA**'])

        deftext = sense_obj.get('definition', {})
        for text in force_list(deftext, 'text'):
            sense.add_feature(xml.Feature("definition", text))
        le.add_sense(sense)

    for wf in obj.get('WordForms', []):
        wordform = xml.WordForm()
        add_features(wf, wordform, ["writtenForm", "msd"])
        le.add_wordform(wordform)

    lmf.add_lexical_entry(le)


def soederwall(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    # xml: remove later, keep for validation? Where to put it in the lmf?
    le.xml = obj['xml']
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        add_features(form, fr, ['lemgram', 'information', 'oldForm', 'gram'])
        add_feature(form, fr, 'writtenForm', 'baseform')
        add_feature_list(form, fr, 'partOfSpeech')
        le.lemma.add_form_representation(fr)

    for sense_obj in obj.get('Sense', []):
        sense = xml.Sense(sense_obj['senseid'])
        add_feature_list(sense_obj, sense, 'gram')
        add_features(sense_obj, sense, ['text', 'V0ISA**'])
        add_feature_list(sense_obj, sense, 'V0IPA**')
        for wf in force_list(sense_obj, 'writtenForm'):
            if wf.strip():
                sense.add_feature(xml.Feature("writtenForm", wf))
        add_feature_list(sense_obj, sense, 'AF0USNI')

        deftext = sense_obj.get('definition', {})
        for text in force_list(deftext, 'text'):
            sense.add_feature(xml.Feature("definition", text))
        le.add_sense(sense)

    for wf in obj.get('WordForms', []):
        wordform = xml.WordForm()
        add_features(wf, wordform, ["msd", "tag"])
        for wf in force_list(wf, 'writtenForm'):
            if wf.strip():
                wordform.add_feature(xml.Feature("writtenForm", wf))
        le.add_wordform(wordform)

    lmf.add_lexical_entry(le)


def soederwallsupp(obj, lmf):
    le = xml.LexicalEntry()
    lemma = xml.Lemma()
    # xml: remove later, keep for validation? Where to put it in the lmf?
    le.xml = obj['xml']
    le.lemma = lemma
    for form in obj['FormRepresentations']:
        fr = xml.FormRepresentation()
        add_features(form, fr, ['lemgram', 'information', 'gram', 'partOfSpeech'])
        add_feature(form, fr, 'writtenForm', 'baseform')
        # add_feature_list(form, fr, 'partOfSpeech')
        le.lemma.add_form_representation(fr)

    for sense_obj in obj.get('Sense', []):
        sense = xml.Sense(sense_obj['senseid'])
        add_feature_list(sense_obj, sense, 'gram')
        add_features(sense_obj, sense, ['text'])
        for wf in force_list(sense_obj, 'writtenForm'):
            if wf.strip():
                sense.add_feature(xml.Feature("writtenForm", wf))
        add_feature_list(sense_obj, sense, 'AF0USNI')

        deftext = sense_obj.get('definition', {})
        for text in force_list(deftext, 'text'):
            sense.add_feature(xml.Feature("definition", text))
        le.add_sense(sense)

    for wf in obj['WordForms']:
        wordform = xml.WordForm()
        add_features(wf, wordform, ["msd", "tag"])
        for wf in force_list(wf, 'writtenForm'):
            if wf.strip():
                wordform.add_feature(xml.Feature("writtenForm", wf))
        le.add_wordform(wordform)

    lmf.add_lexical_entry(le)


def termswefin(obj, lmf):
    lmf.useNamespace = True
    lmf.dtd = xml.sb_dtd

    def do_sourceform(form, le):
        lang = lang_encode(form['lang'])
        form_representation = xml.FormRepresentation()
        form_representation.add_attrib(xml.Attribute('xml:lang', lang))
        form_representation.add_feature(xml.Feature('type', 'source'))
        form_representation.add_feature(xml.Feature('writtenForm', form.get('form')[0].get('wordform')))
        add_feature(form.get('form')[0], form_representation, 'comment')
        to_add = ['definition', 'example', 'source']
        add_features(form, form_representation, to_add)
        le.lemma.add_form_representation(form_representation)

    def do_targetform(form, le):
        lang = lang_encode(form['lang'])
        if 'example' in form or 'source' in form:
            form_representation1 = xml.FormRepresentation()
            to_add = ['example', 'source']
            form_representation1.add_attrib(xml.Attribute('xml:lang', lang))
            form_representation1.add_feature(xml.Feature('type', 'target'))
            add_features(form, form_representation1, to_add)
            le.lemma.add_form_representation(form_representation1)

        for wform in form.get('form'):
            form_representation = xml.FormRepresentation()
            form_representation.add_attrib(xml.Attribute('xml:lang', lang))
            form_representation.add_feature(xml.Feature('type', 'target'))
            form_representation.add_feature(xml.Feature('writtenForm', wform.get('wordform')))
            add_feature(wform, form_representation, 'comment')
            le.lemma.add_form_representation(form_representation)

    le = xml.LexicalEntry()
    le.lemma = xml.Lemma()
    single_topfeatures = ['lastmodified', 'lastmodifiedBy']
    add_features(obj, le, single_topfeatures)
    for subtype in obj.get('subtype', []):
        le.add_feature(xml.Feature('entryType', subtype))
    add_features(obj, le, ['termstatus', 'terminternalcomment'])

    do_sourceform(obj['baselang'], le)

    for form in obj.get('targetlang'):
        do_targetform(form, le)

    sense = xml.Sense('')
    examples = {}
    for ex in [obj.get('baselang')]+obj.get('targetlang'):
        lang = lang_encode(ex.get('lang', ''))
        if lang in examples:
            print('Error, to many representations of %s, %s' % (lang, ex['wordform']))
        examples[lang] = ex.get('compound', [])

    for n in range(max([len(x) for x in examples.values()])):
        sense_ex = xml.SenseExample(_type="compound")
        for lang, ex in examples.items():
            sense_ex.add_example(example=ex[n], lang=lang)
        sense.add_sense_example(sense_ex)

    le.add_sense(sense)
    lmf.add_lexical_entry(le)


def mklmf(objects, lexfunc, lang='swe'):
    lmf = xml.LMF(lang)
    for obj in objects:
        try:
            if type(obj) != dict:
                try:
                    obj = json.loads(obj)
                except Exception as e:
                    raise e
            lexfunc(obj, lmf)
        except Exception as e:
            print('obj', obj, file=sys.stderr)
            raise e
    return str(lmf)


lex_dict = {'saldo'           : saldo,
            'saldoe'          : saldoe,
            'saldom'          : saldom,
            'swesaurus'       : swesaurus,
            'parolelexplus'   : parole,
            'simpleplus'      : simple,
            'kelly'           : kelly,
            'wordnet-saldo'   : wordnet,
            'diapivot'        : diapivot,
            'dalin-base'      : dalinbase,
            'dalinm'          : saldom,
            'swedbergm'       : saldom,
            'ao'              : ao,
            'fsvm'            : saldom,
            'lexin_multi'     : lexin,
            'lexin'           : lexin,
            'term-swefin'     : termswefin,
            'lwt'             : lwt,
            'blissword'       : bliss,
            'blisschar'       : bliss,
            'blingbring'      : blingbring,
            'dalin'           : dalin,
            'schlyter'        : schlyter,
            'sentimentlex'    : sentimentlex,
            'soederwall'      : soederwall,
            'soederwall-supp' : soederwall,
            'swedberg'        : swedberg,
            'hellqvist'       : hellqvist,
            'swefn'           : swefn,
            'konstruktikon'   : konstruktikon,
            'konstruktikon-rus'   : konstruktikonrus,
            'konstruktikon-multi'   : konstruktikonrus
           }

lex_lang = {'fsvm': 'fsv'}

if __name__ == "__main__":
    if sys.argv[1] == '--convert':
        name = sys.argv[2]
        data = sys.stdin.readlines()
        lang = 'swe'
        if len(sys.argv) > 3:
            lang = sys.argv[3]
        lmf = mklmf(data, lex_dict[name], lang=lang)
        print(lmf)

    elif sys.argv[1] == '--cmp':
        old = etree.parse(sys.argv[2]).getroot()
        new = etree.parse(sys.argv[3]).getroot()
        errors = []
        xmldiff.etree_compare(old, new, '', 0, errors)
        if errors:
            open('cmpdiff.txt', 'w').write('\n'.join(errors))
            print('\n\ndiff between files. See file %s' % ('cmpdiff.txt'))
        else:
            print('\n\nok!')

    elif sys.argv[1] == '--mklmf':
        lexicon = sys.argv[2]
        data = json.loads(sys.stdin.read())
        lang = lex_lang.get(lexicon, 'swe')
        lmf = mklmf(data, lex_dict[lexicon], lang=lang)
        print(lmf)

    else:
        print('Don\'t know what to do.')
