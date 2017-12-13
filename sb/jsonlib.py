#!/usr/bin/env python
# -*- coding: utf8 -*-

import cgi
import json
import re


class JSON:
    def __init__(self, lang=''):
        self.lang = lang
        self.lexical_entries = []
        self._lexical_entries_set = set()
        self._le_senses = set()
        # self.semantic_predicates = []
        # namespacing is not used at the moment
        # all needed spaces can (should be able to) be added at a later stage
        self.useNamespace = False
        self.namespaces = {}

    def add_lexical_entry(self, lexical_entry):
        self.lexical_entries.append(lexical_entry)
        # Ett fulhack for att speeda upp det lite
        # (ersatt med nagot battre i framtiden)
        self._lexical_entries_set.add(".".join([lexical_entry._pos,
                                                lexical_entry._wf]))
        self.namespaces.update(lexical_entry.namespaces)

    def add_namespace(self, name, space):
        self.namespaces[name] = space

    def __unicode__(self):  # use unicode instead of string because to
                            # make compatible with python2
        # TODO make use of this namespace??
        if self.useNamespace:
            for n, s in self.namespaces.items():
                ns = ' '.join(('%s:%s' % (n, s)
                               for n, s in self.namespaces.items()))
        else:
            ns = ''

        return '[\n%s\n]' % ",".join([unicode(e) for e in self.lexical_entries])


class LexicalEntry:
    def __init__(self, name='', order=''):
        self.components = []
        self.entrytype = ''
        self.etymology = ''
        self.features = []
        self.idattr = ""
        self.lemma = None
        self.name = name
        self.namespaces = {}
        self.order = order
        self.saldolinks = ""
        self.senses = []
        self.wordforms = []
        self.xml = ''
        self._pos = ""
        self._wf = ""

    def add_sense(self, sense):
        self.senses.append(sense)
        self.namespaces.update(sense.namespaces)

    def add_feature(self, feature):
        self.features.append(feature)

    def add_etymology(self, etymology):
        self.etymology = etymology

    def add_feature_unique(self, feature):
        for existing_feature in self.features:
            if(existing_feature.att == feature.att and
               existing_feature.val == feature.val):
                return
        self.add_feature(feature)

    def set_entrytype(self, _type):
        self.entrytype = _type

    def get_components(self):
        if self.components:
            return '"ListOfComponents" : [%s]' %\
                   ','.join([unicode(c) for c in self.components])
        else:
            return ''

    def add_component(self, component):
        self.components.append(component)

    def add_wordform(self, wordform):
        self.wordforms.append(wordform)

    def add_saldoLinks(self, saldoLinks):
        self.saldolinks = saldoLinks
        self.namespaces.update(saldoLinks.namespaces)

    def __unicode__(self):
        content = []
        components = self.get_components()
        content.append('"lexiconOrder" : "%s"' % self.order)
        if components:      content.append(components)
        if self.features:   content.append(unicode(Features(self.features)))
        if self.idattr:     content.append('"id" : %s' % (self.idattr))
        if self.wordforms:  content.append(unicode(WordForms(self.wordforms)))
        if self.lemma:      content.append(unicode(self.lemma))
        if self.senses:     content.append(unicode(Senses(self.senses)))
        if self.saldolinks: content.append(unicode(self.saldolinks))
        if self.name:       content.append('"lexiconName" : "%s"' % self.name)
        if self.entrytype:  content.append('"entryType" : "%s"' % self.entrytype)
        if self.etymology:  content.append(unicode(self.etymology))
        if self.xml:        content.append('"xml" : %s' % escape(self.xml))
        return '{%s}' % ','.join(content)

    def __str__(self):
        return unicode(self).encode('utf-8')


# class Attribute:
#     def __init__(self, key, val):
#         self.key = key
#         self.val = val
#
#     def __unicode__(self):
#         return '%s="%s"' % (self.key, escape(self.val))

class Component:
    def __init__(self, ref):
        self.ref = ref
        self.namespaces = {}

    def __unicode__(self):
        return '{"Component" : {"entry" : "%s"}}' % (self.ref)


class SaldoLinks:
    def __init__(self):
        self.namespaces = {'karp': "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp"}
        self.saldo_id = []

    def add(self, saldo_id):
        self.saldo_id.append(quote(saldo_id))

    def __unicode__(self):
        return '"saldoLinks" : [%s]' % (','.join(self.saldo_id))


class Lemma:
    def __init__(self):
        self.form_representations = []
        self.objects = []   # other/external types of objects

    def add_form_representation(self, form_representation):
        self.form_representations.append(form_representation)

    def add_object(self, obj):
        self.objects.append(obj)

    def __unicode__(self):
        obj = ''
        if self.objects:
            obj = ', '.join([unicode(o) for o in self.objects])
            if not self.form_representations:
                return obj
            obj += ', '

        return obj + '"FormRepresentations" : [%s]'\
               % ','.join(unicode(fr) for fr in self.form_representations)


class WordForm:
    def __init__(self):
        self.features = []
        self.form_representations = []

    def add_feature(self, feature):
        self.features.append(feature)

    def add_form_representation(self, form_representation):
        self.form_representations.append(form_representation)

    def __unicode__(self):
        content = []
        if self.form_representations:
            content.append(','.join(unicode(fr)
                           for fr in self.form_representations))
        if self.features:
            content.append(unicode(Features(self.features)))
        return '{%s}' % (",".join(content))


class WordForms:
    def __init__(self, wordforms):
        self.wordforms = wordforms

    def __unicode__(self):
        content = []
        if self.wordforms:
            content.append(','.join(unicode(ws) for ws in self.wordforms))
        return '"WordForms" : [%s]'\
               % ','.join(unicode(w) for w in self.wordforms)


class FormRepresentation:
    def __init__(self):
        self.features = []
        self.attribs  = []
        self.objects = []  # for non standard things

    def add_feature(self, feature):
        self.features.append(feature)

    def add_feature_unique(self, feature):
        for existing_feature in self.features:
            if(existing_feature.att == feature.att and existing_feature.val == feature.val):
                return
        self.add_feature(feature)

    def add_attrib(self, attrib):
        self.attribs.append(attrib)

    def add_object(self, obj):
        self.objects.append(obj)

    def __unicode__(self):
        if self.features or self.objects:
            content = []
            if self.attribs:
                content.extend([unicode(a) for a in self.attribs])
            if self.features:
                content.append(unicode(Features(self.features)))
            if self.objects:
                content.extend([unicode(o) for o in self.objects])
            return '{%s}' % ','.join(content)
        else:
            return ''


class BlingBringRoget:
    def __init__(self, head_id):
        self.head_id = head_id

    def __unicode__(self):
        roget = self.head_id.split('/')
        rogetobj = {"id": '/'.join(roget), "class": roget[0],
                    "section": roget[1], "subsection": roget[2],
                    "headgroup": roget[3], "head": roget[4],
                    "name": roget[5]}
        return '"roget":' + json.dumps(rogetobj)


class BlingBringBring:
    def __init__(self, entry_id):
        self.entry_id = entry_id

    def __unicode__(self):
        bring = self.entry_id.split('/')
        bringobj = {"id": '/'.join(bring), "class": bring[0],
                    "partOfSpeech": bring[1], "group": bring[2],
                    "groupposition": bring[3]}
        return '"bring":' + json.dumps(bringobj)


class FeatureExtra:
    # extra is a tuple, swefn
    def __init__(self, att, val, extra=None):
        self.att = att
        self.val = val
        self.extra = extra

    def str_val(self):
        if self.extra is None:
            return '{"val": %s}' % escape(self.val)
        else:
            return '{"val": %s, "%s" : "%s"}'\
                   % (escape(self.val), self.extra[0], self.extra[1])

    def __unicode__(self):
        if self.extra is None:
            return '"%s" :  {"val": %s}' % (self.att, escape(self.val))
        else:
            return '"%s" : {"val": %s, "%s" : "%s"}'\
                   % (self.att, escape(self.val), self.extra[0], self.extra[1])


class FeaturesExtra:
    def __init__(self, feats):
        self.feats = {}
        for feat in feats:
            if feat.att not in self.feats:
                self.feats[feat.att] = []
            self.feats[feat.att].append(feat.str_val())

    def __unicode__(self):
        return ','.join('"%s" : [%s]'
                        % (k, ','.join(v)) for k, v in self.feats.items())


class Feature:
    def __init__(self, att, val, forcelist=False):
        self.att = att
        self.val = val
        self.forcelist = forcelist

    def __unicode__(self):
        return '"%s" : %s' % (self.att, escape(self.val))


class Features:
    def __init__(self, feats):
        self.feats = {}
        for feat in feats:
            oldv = self.feats.get(feat.att)
            if isinstance(oldv, list):
                self.feats[feat.att] += ['%s' % feat.val]
            elif oldv:
                self.feats[feat.att] = [oldv, '%s' % feat.val]
            elif feat.forcelist:
                self.feats[feat.att] = ['%s' % feat.val]
            else:
                self.feats[feat.att] = '%s' % feat.val

    def __unicode__(self):
        return ','.join(featlistquote(kv) for kv in self.feats.items())


def featlistquote(kv):
    # TODO the commented out section below is solved by jsons dumps?
    # if isinstance(kv[1], list):
    #     return '"%s" : [%s]' % (kv[0], escape(kv[1]))
    # # for python2
    # # kv1 = kv[1].encode('utf8') if type(kv[1]) is unicode else kv[1]
    # kv1 = kv[1]
    return '"%s" : %s' % (kv[0], escape(kv[1]))


class Sense:
    # allow_many_defs should only be true for older lexica (eg. dalin)
    def __init__(self, sense, allow_many_defs=False):
        self.sense = sense
        self.relations = []
        self.swesaurus_relations = []
        self.predicative_representations = []
        self.sense_examples = []
        self.examples = {}  # new
        self.definitions = {}  # new
        self.features = []
        self.extrafeatures = []  # swefn
        self.xml = []
        self.attribs = []
        self.ext_const_elems = []
        self.int_const_elems = []
        self.namespaces = {}
        self.allow_many_defs = allow_many_defs  # dalin

    def add_sense_relation(self, sense_relation):
        self.relations.append(sense_relation)

    def add_swesaurusrelation(self, swe_relation):
        self.swesaurus_relations.append(swe_relation)

    def add_definition_xml(self, xml, lang=''):
        if lang:
            self.definitions[lang+'_xml'] = '"%s"' % xml
        elif 'xml' not in self.definitions:
            self.definitions['xml'] = '"%s"' % xml
            # self.definitions['xml'] = json.dumps(xml)
        else:
            raise Exception('%s %s %s' %
                            ('too many definitions!!', self.definitions, xml))
        # self.examples['xml'].append(xml)

    def add_definition_text(self, text):
        if 'text' not in self.definitions:
            self.definitions['text'] = escape(text)
        elif self.allow_many_defs:
            if type(self.definitions['text']) is list:
                self.definitions['text'] += escape(text)
            else:
                self.definitions['text'] = [self.definitions['text'],
                                            escape(text)]
        else:
            raise Exception('%s %s %s' %
                            ('too many definitions!!', self.definitions, text))

    def add_example_xml(self, xml):
        if 'xml' not in self.examples:
            self.examples['xml'] = []
        self.examples['xml'].append(xml)

    # def add_predicative_representation(self, predicative_representation):
    #     self.predicative_representations.append(predicative_representation)

    def add_sense_example(self, sense_example):
        self.sense_examples.append(sense_example)

    def add_feature(self, feature):
        self.features.append(feature)

    def add_extrafeature(self, feature):
        self.extrafeatures.append(feature)

    def add_attrib(self, attrib):
        self.attribs.append(attrib)

    def add_ext_const_elems(self, items):
        self.ext_const_elems.append(items)

    def add_int_const_elems(self, items):
        self.int_const_elems.append(items)

    # def add_from_xml(self, xml):
    #    self.xml.append(xml)

    def __unicode__(self):
        content = []
        if self.sense:
            content.append('"senseid" : "%s"' % self.sense)
        if self.relations:
            content.append(unicode(SenseRelations(self.relations)))
        if self.swesaurus_relations:
            content.extend((unicode(s) for s in self.swesaurus_relations))
        if self.sense_examples:
            content.append(unicode(SenseExamples(self.sense_examples)))
        if self.features:
            content.append(unicode(Features(self.features)))
        if self.extrafeatures:
            content.append(unicode(FeaturesExtra(self.extrafeatures)))
        # if self.xml:
        #     content.extend([xml_to_string(ex, self) for ex in self.xml])
        if self.examples:
            ex = []
            for k, values in self.examples.items():
                ex.append(','.join('{"%s": "%s"}' % (k, v) for v in values))
            content.append('"examples" : [%s]' % ','.join(ex))
        if self.definitions:
            defs = []
            lang_defs = []
            for key, val in self.definitions.items():
                if type(val) is list:  # true only for dalin&co.
                    defs.append('"%s" : [%s]'
                                % (key, ','.join('%s' % v for v in val)))
                elif key.endswith('_xml'):
                    lang_defs.append((key[:-4], '"%s" : %s' % ("xml", val)))
                else:
                    defs.append('"%s" : %s' % (key, val))
            content.append('"definition" : {%s}' % ','.join(defs))
            for lang, ldef in lang_defs:
                content.append('"definition_%s" : {%s}' % (lang, ldef))
        ints, exts = [], []
        for int_const in self.int_const_elems:
            ints.append(['"%s" : %s' % (k, escape(v)) for k, v in int_const])
        if ints:
            content.append('"int_const_elem" : [%s]'
                           % ','.join('{%s}' % ','.join(i) for i in ints))
        for ext_const in self.ext_const_elems:
            exts.append(['"%s" : %s'
                         % (k, escape(v)) for k, v in ext_const])
        if exts:
            content.append('"ext_const_elem" : [%s]'
                           % ','.join('{%s}' % ','.join(i) for i in exts))

        return '{%s}' % ",".join(content)


class Senses:
    def __init__(self, senses):
        self.senses = senses

    def __unicode__(self):
        return '"Sense" : [%s]' % ','.join(unicode(s) for s in self.senses)


class SenseRelation:
    # TODO support for primary/secondary children
    def __init__(self, val='', labels=[]):
        self.values = []
        for lab in labels:
            self.values.append((lab, val))

    def add_value(self, label, val):
        self.values.append((label, val))

    def __unicode__(self):
        content = []
        for lab, val in self.values:
            if lab == 'primary':  # saldo
                content.append('"%s" : "%s"' % (lab, val))
            elif lab == 'secondary':  # saldo
                content.append('"%s" : [%s]'
                               % (lab, ','.join('"%s"' % v for v in val)))
            else:  # dalin
                content.append('"%s" : [%s]'
                               % (lab, ','.join('"%s"' % v for v in val)))
        return ','.join(content)


class SenseRelations:
    def __init__(self, relations=[]):
        self.relations = relations

    def add_relations(self, relation):
        self.relations.append(relation)

    # TODO  Should always be a list, but check that this is ok with saldo first
    def __unicode__(self):
        return '"SenseRelations" : {%s}'\
               % ','.join(unicode(rel) for rel in self.relations)


class SwesaurusRelations:
    def __init__(self):
        self.relations = []

    def add_relations(self, target, relations):
        self.relations.append((target, relations))

    def __unicode__(self):
        relations = []
        for target, rel in self.relations:
            relations.append('{"targets" : "%s", %s}' % (target,
                             ', '.join('"%s": "%s"' % (r, v) for r, v in rel)))
        return '"SenseRelations" : [%s]'\
               % ','.join(unicode(rel) for rel in relations)


class SenseExample:
    def __init__(self, text='', lang='', _type='', _id=''):
        self.example = text
        self.lang = lang
        self.feats = []
        self._type = _type
        self._id = _id

    def set_lang(self, lang):
        self.lang = lang

    def set_id(self, _id):
        self._id = _id

    def add_feat(self, feat):
        self.feats.append(feat)

    def __unicode__(self):
        components = []
        if self.example:
            components.append('"text" : %s' % escape(self.example))
        if self._type:
            components.append('"type" : "%s"' % self._type)
        if self.lang:
            components.append('"lang" : "%s"' % self.lang)
        if self._id:
            components.append('"example_id" : "%s"' % self._id)
        if self.feats:
            components.append(unicode(Features(self.feats)))
        return ','.join(components)


class SenseExamples:
    def __init__(self, examples):
        self.examples = examples

    def __unicode__(self):
        return '"SenseExamples" : [%s]'\
               % ','.join('{%s}' % unicode(e) for e in self.examples)


class Etymology:
    def __init__(self):
        self.etymons = []

    def add_etymon(self):
        etymon = Etymon()
        self.etymons.append(etymon)
        return etymon

    def __unicode__(self):
        strs = []
        for i, etymon in enumerate(self.etymons):
            etymon.set_id(str(i))
            strs.append(unicode(etymon))

        return '"Etymology" : {"etymon": [%s]}' % ', '.join(strs)


class Etymon:
    def __init__(self):
        self.forms = []
        self.etymid = ''

    def add_form(self, lang, form, desc=''):
        self.forms.append((lang, form, desc))

    def set_id(self, etymid):
        self.etymid = etymid

    def __unicode__(self):
        etymon_str = []
        for lang, form, desc in self.forms:
            descjson = cgi.escape(', "desc": "%s"' % desc if desc else '')
            etymon_str.append('{"lang": "%s", "form": "%s"%s}' %
                               (lang, form.strip(), descjson))
        return '[%s]' % ', '.join(etymon_str)


# HELPER FUNCTIONS ------------------------------------------------------------
def escape(s):
    return json.dumps(s, ensure_ascii=False)

    # TODO all lexicons should be correctly escaped by now (170405)
    #      this function will not be used anymore
    # TODO this function is made for lexicons like hellqvist
    # where the ocr has made random baskslashes etc.
    # It should be improved and simplified when the errors are
    # removed from all lexicons. It should also be tested so
    # that converting a lexicon back and forth does not insert
    # superfluous backslashes.
    # s = s.replace('&', '&amp;')
    # s = s.replace("'", "\\'")
    # s = s.replace('<', '&lt;')
    # s = s.replace('>', '&gt;')
    #  remove instances like '\ ' and '\.'
    # s = unescape(s) # avoid double escaping
    # s = re.sub('\([^\\])\\\([ .])',r'\1\\\\\2',s)
    # s = re.sub('([^\\])\n([^\\])', r'\1\\\\n\2',s)
    # s = re.sub('([^\\])\t([^\\])', r'\1 \2',s)
    # s = re.sub('([^\\])\\\\([^\\])', r'\1\\\\\\\\\2',s)
    # Single backslashes before whitespaces or full stop should be escaped
    # s = re.sub('[^\\\]\\\([ .])', r'\\\\\1', s)
    # s = re.sub('[^\\\]\n', '\\\\n', s)
    # s = re.sub('\t', ' ', s)
    # s = re.sub('(?!\\\)"', '\\"', s)
    # s = re.sub('\\\\', '\\\\\\\\', s)
    # return s  #s.replace('[^\\\]"', '\\"')


# def unescape(s):
#     s = re.sub('\\\\', '\\', s)
#     s = re.sub('\\\\n', '\n', s)
#     s = re.sub('\\\\\\\\', '\\\\', s)
#     return s
#


def quote(val):
    return '"%s"' % val


def xml_to_string(xml, lmfobj):
    """ Converts a valid a xml blob into a string
        Removes namespace definitions from this xml snippet
        but saves the information for later usage
    """
    if type(xml) is bytes:  # konstruktikon has byte for some reason??
        xml = unicode(xml)
    ns = re.findall('xmlns:(.*?)="(.*?)"', xml)
    for name, space in ns:
        lmfobj.namespaces[name] = space
        xml = re.sub('xmlns:.*?=".*?"', '', xml)
    return xml


def add_features(entry, target, names):
    for name in names:
        add_feature(entry, target, name)


def add_feature(entry, target, name, fromname=''):
    if not fromname:
        fromname = name
    for feat in entry.findall("feat"):
        if feat.get("att") == fromname:
            target.add_feature(Feature(name, re.sub('"', '\\"',
                                                    feat.get("val"))))

def findfeat(entry, att):
    for feat in entry.findall("feat"):
        if feat.get("att") == att:
            return feat.get("val")
    return ''


def findfeatlist(entry, att):
    res = []
    for feat in entry.findall("feat"):
        if feat.get("att") == att:
            res.append(feat.get("val"))
    return res


# DONT USE THIS, ADD_FEATURE IS THE CORRECT ONE
def add_feature_list(entry, target, name):
    for toadd in entry.findall(name):
        target.add_feature(Feature(name, toadd))


# For compatibility with python3 :(
def unicode(obj):
    return obj.__unicode__()
