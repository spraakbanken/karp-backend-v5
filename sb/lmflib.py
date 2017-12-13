#!/usr/bin/env python
# -*- coding: utf8 -*-

import html
import re
sb_dtd = "https://svn.spraakdata.gu.se/sb-arkiv/pub/lmf/dtd/DTD_SB_LMF_REV_16.dtd"


class LMF:
    def __init__(self, lang):
        self.lang = lang
        self.lexical_entries = []
        self._lexical_entries_set = set()
        self._le_senses = set()
        self.semantic_predicates = []
        # namespacing is not used at the moment
        # all needed spaces can (should be able to) be added at a later stage
        self.useNamespace = False
        self.namespaces = {}
        self.dtd = ''

    def add_lexical_entry(self, lexical_entry):
        self.lexical_entries.append(lexical_entry)
        # Ett fulhack for att speeda upp det lite (ersatt med nagot battre i
        # framtiden):
        self._lexical_entries_set.add(".".join([lexical_entry._pos,
                                                lexical_entry._wf]))
        self.namespaces.update(lexical_entry.namespaces)

    def add_semantic_predicate(self, semantic_predicate):
        self.semantic_predicates.append(semantic_predicate)

    def add_namespace(self, name, space):
        self.namespaces[name] = space

    def __str__(self):
        if self.useNamespace:
            ns = ' '.join(('xmlns:%s="%s"' % (n,s) for n,s in self.namespaces.items()))
        else:
            ns = ''
        if self.dtd:
            dtd = '<!DOCTYPE dtd SYSTEM "%s">' % self.dtd
        else:
            dtd = ''
        return "\n".join([
                         '<?xml version="1.0" encoding="UTF-8"?>',
                         dtd,
                         '<!-- $Date$ -->',
                         '<LexicalResource dtdVersion="16">',
                         '<GlobalInformation>',
                         ' <feat att="languageCoding" val="ISO 639-3"/>',
                         '</GlobalInformation>',
                         '<Lexicon %s>' % ns,
                         ' <feat att="language" val="%s"/>' % self.lang,
                         "\n".join([str(e) for e in self.lexical_entries]),
                         "\n".join([str(s) for s in self.semantic_predicates]),
                         '</Lexicon>',
                         '</LexicalResource>'
                         ])
#  '<Lexicon xmlns:karp="http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp">',


class LexicalEntry:
    def __init__(self):
        self.components = []
        self.etymology = ''
        self.features = []
        self.idattr = ""
        self.namespaces = {}
        self.lang = ""
        self.lemma = None
        self.relatedform = []
        self.saldolinks = []
        self.senses = []
        self.wordforms = []
        self.xml = ""  # for raw xml blobs as in dalin
        self._pos = ""
        self._wf = ""

    def set_lang(self, lang):
        self.lang = lang

    def add_sense(self, sense):
        self.senses.append(sense)
        self.namespaces.update(sense.namespaces)

    def add_etymology(self, etymology):
        self.etymology = etymology

    def add_feature(self, feature):
        self.features.append(feature)

    def add_feature_unique(self, feature):
        for existing_feature in self.features:
            if(existing_feature.att == feature.att and existing_feature.val == feature.val):
                return
        self.add_feature(feature)

    def get_components(self):
        if self.components:
            return '\n'.join(['<ListOfComponents>',
                              '\n'.join([str(c) for c in self.components]),
                              '</ListOfComponents>'])
        else:
            return ''

    def add_component(self, component):
        self.components.append(component)

    def add_wordform(self, wordform):
        self.wordforms.append(wordform)

    def add_saldoLink(self, saldoLink):
        self.saldolinks.append(saldoLink)
        self.namespaces.update(saldoLink.namespaces)

    def add_relatedform(self, form):
        self.relatedform = form

    def __str__(self):
        attrs = ''
        if(self.idattr):
            attrs += 'id="%s" ' % (self.idattr)
        if(self.lang):
            attrs += 'xml:lang="%s"' % (self.lang)
        le_string = '<LexicalEntry %s>' % attrs
        xmlblock = ''
        if self.xml:
            xmlblock = '<xml>'+self.xml+'</xml>'
        return "\n".join([
            le_string,
            xmlblock,
            '\n'.join([str(f) for f in self.features]),
            self.get_components(),
            str(self.lemma),
            '\n'.join([str(w) for w in self.wordforms]),
            '\n'.join([str(s) for s in self.senses]),
            '\n'.join([str(f) for f in self.saldolinks]),
            str(self.etymology),
            str(self.relatedform or ''),
            '</LexicalEntry>'])


class Attribute:
    def __init__(self, key, val):
        self.key = key
        self.val = val

    def __str__(self):
        return '%s="%s"' % (self.key, escape(self.val))


class Component:
    def __init__(self, ref):
        self.ref = ref
        self.namespaces = {}

    def __str__(self):
        return '<Component entry="%s"/>' % (self.ref)


class SaldoLink:
    def __init__(self, saldo_id):
        self.namespaces = {'karp': "http://spraakbanken.gu.se/eng/research/infrastructure/karp/karp"}
        self.saldo_id = saldo_id

    def __str__(self):
        return '<karp:saldoLink ref="%s"/>' % (self.saldo_id)

# class ListOfComponents:
#     def __init__(self):
#         self.components = []
#
#     def addComponent(self, component):
#         self.components.append(component)
#
#     def __str__(self):
#         return '\n'.join(['<ListOfComponents>',
#                           ', '.join([str(c) for c in self.components]),
#                           '</ListOfComponents>'
#                           ])


class RelatedForm:
    def __init__(self, ref, label='se'):
        self.ref = ref
        self.label = label

    def __str__(self):
        return "\n".join(['<RelatedForm>',
                          str(Feature(self.label, self.ref)),
                          '</RelatedForm>'])


class Lemma:
    def __init__(self):
        self.form_representations = []
        self.features = []  # now including writtenForm and partOfSpeech!

    def add_feature(self, feature):
        self.features.append(feature)

    def add_feature_unique(self, feature):
        for existing_feature in self.features:
            if(existing_feature.att == feature.att and existing_feature.val == feature.val):
                return
        self.add_feature(feature)

    def add_form_representation(self, form_representation):
        self.form_representations.append(form_representation)

    def __str__(self):
        if self.features or self.form_representations:
            return "\n".join(['<Lemma>',
                              '\n'.join(str(fr) for fr in self.form_representations),
                              '</Lemma>'])

            # return "\n".join(['<Lemma>\n<FormRepresentation>',
            #                   '\n'.join([str(f) for f in self.features]),
            #                   '</FormRepresentation>\n</Lemma>'])
        else:
            return '<Lemma/>'


class WordForm:
    def __init__(self):
        self.features = []
        self.form_representations = []

    def add_feature(self, feature):
        self.features.append(feature)

    def add_form_representation(self, form_representation):
        self.form_representations.append(form_representation)

    def __str__(self):
        return "\n".join(['<WordForm>',
                          '\n'.join(str(fr) for fr in self.form_representations),
                          '\n'.join([str(f) for f in self.features]),
                          '</WordForm>'])


class FormRepresentation:
    def __init__(self):
        self.features = []
        self.attribs  = []

    def add_feature(self, feature):
        self.features.append(feature)

    def add_feature_unique(self, feature):
        for existing_feature in self.features:
            if(existing_feature.att == feature.att and existing_feature.val == feature.val):
                return
        self.add_feature(feature)

    def add_attrib(self, attrib):
        self.attribs.append(attrib)

    def __str__(self):
        if self.features:
            attribs = ' '.join([str(a) for a in self.attribs])
            return "\n".join(['<FormRepresentation %s>' % attribs,
                              '\n'.join([str(f) for f in self.features]),
                              '</FormRepresentation>'])
        else:
            attribs = ' '.join([str(a) for a in self.attribs])
            return '<FormRepresentation %s/>' % attribs


class Feature:
    # extra is a tuple
    def __init__(self, att, val, extra=None):
        self.att = att
        self.val = val
        self.extra = extra

    def __str__(self):
        if self.extra is None:
            return '<feat att="%s" val="%s"/>' % (self.att, escape(self.val))
        else:
            return '<feat att="%s" val="%s" %s="%s"/>' % (self.att,
                                                          escape(self.val),
                                                          self.extra[0],
                                                          self.extra[1])


class Sense:
    def __init__(self, sense):
        self.sense = sense
        self.relations = []
        self.predicative_representations = []
        self.sense_examples = []
        self.semantic_labels = []
        self.examples = []  # new
        self.definitions = []  # new
        self.features = []
        self.xml = []
        self.attribs = []
        self.ext_const_elems = []  # konstruktikon
        self.int_const_elems = []  # konstruktikon
        self.namespaces = {}

    def add_sense_relation(self, sense_relation):
        self.relations.append(sense_relation)

    def add_predicative_representation(self, predicative_representation):
        self.predicative_representations.append(predicative_representation)

    def add_sense_example(self, sense_example):
        self.sense_examples.append(sense_example)

    def add_semantic_label(self, semantic_label):
        self.semantic_labels.append(semantic_label)

    def add_feature(self, feature):
        self.features.append(feature)

    def add_attrib(self, attrib):
        self.attribs.append(attrib)

    def add_from_xml(self, xml, lang=''):
        if lang:
            xml = re.sub('^<(.*?)>', r'<\1 xml:lang="%s">' % lang, xml)

        self.xml.append(xml)

    def add_definition_text(self, text):
        self.features.append(Feature("definition", text))

    def add_int_const_elem(self, int_const):
        self.int_const_elems.append(int_const)

    def add_ext_const_elem(self, ext_const):
        self.ext_const_elems.append(ext_const)

    def __str__(self):
        sense_id = 'id="%s"' % self.sense if self.sense else ''
        if not self.relations and not self.predicative_representations and not self.sense_examples and not self.features and not self.xml and not self.semantic_labels:
            return '<Sense %s %s/>' % (sense_id, ' '.join([str(a) for a in self.attribs]))
        else:
            contents = []
            if self.xml:
                contents.append("\n".join([xml_to_string(ex,self) for ex in self.xml]))
            if self.int_const_elems:
                contents.append("\n".join([str(i) for i in self.int_const_elems]))
            if self.ext_const_elems:
                contents.append("\n".join([str(e) for e in self.ext_const_elems]))
            return "\n".join(['<Sense %s %s>' % (sense_id, ' '.join([str(a) for a in self.attribs])),
                              "\n".join([str(f) for f in self.features]),
                              "\n".join([str(pre) for pre in self.predicative_representations]),
                              "\n".join([str(rel) for rel in self.relations]),
                              "\n".join([str(ex) for ex in self.sense_examples]),
                              "\n".join([str(ex) for ex in self.semantic_labels]),
                              "\n".join(contents),
                              '</Sense>'
                              ])


class SenseRelation:
    def __init__(self, target, relation_types):
        self.target = target
        self.relation_types = relation_types
        self.features = []

    def add_feature(self, feature):
        self.features.append(feature)

    def __str__(self):
        return "\n".join(['<SenseRelation targets="%s">' % (self.target),
                          '\n'.join(['<feat att="label" val="%s"/>' % t for t in self.relation_types]),
                          '\n'.join([str(f) for f in self.features]),
                          '</SenseRelation>'
                          ])


class SenseExample:
    def __init__(self, example='', tag='', _type='', lang=''):
        # Dalin has many examples text per SenseExample, which share tag and
        # type. To deal with this, self.examlpe is a list instead of a string
        self.example = []
        if example:
            self.example = [(example, lang)]
        self.tag = tag
        self._type = _type
        self.feats = []

    def add_example(self, example, lang=''):
        self.example.append((example, lang))

    def add_tag(self, tag):
        self.tag = tag

    def add_type(self, _type):
        self._type = _type

    def add_feature(self, feat):
        self.feats.append(feat)

    def __str__(self):
        feats = []
        for ex, lang in self.example:
            if lang:
                feats.append('<feat att="text" val="%s" xml:lang="%s"/>' % (escape(ex), lang))
            else:
                feats.append('<feat att="text" val="%s"/>' % escape(ex))
        if self.tag:
            feats.append('<feat att="tag" val="%s"/>' % escape(self.tag))
        if self._type:
            feats.append('<feat att="type" val="%s"/>' % escape(self._type))
        if self.feats:
            feats.extend([str(feat) for feat in self.feats])
        return "\n".join(['<SenseExample>',
                          '\n'.join(feats),
                          '</SenseExample>'
                          ])


class IntConstElem:
    def __init__(self, arguments):
        self.elems = arguments

    def __str__(self):
        # keys starting with $$ are junk from angular, ignore them
        # (the cleanup can be removed when the frontend has stopped putting them there)
        elems = ['%s="%s"' % (k, escape(v)) for k,v in self.elems.items() if not k.startswith('$$')]
        return '<konst:int_const_elem %s/>' % ' '.join(elems)


class ExtConstElem:
    def __init__(self, arguments):
        self.elems = arguments

    def __str__(self):
        return '<konst:ext_const_elem %s/>' % ' '.join('%s="%s"' % (k, escape(v)) for k,v in self.elems.items())


class SemanticPredicate:
    def __init__(self, id, domain, semantic_types):
        self.id = id
        # self.domain = domain
        self.semantic_types = semantic_types
        self.semantic_arguments = []
        self.features = []
        if domain is not None and domain != "":
            self.add_feature(Feature("domain", domain))

    def add_semantic_argument(self, argument):
        self.semantic_arguments.append(argument)

    def add_feature(self, feature):
        self.features.append(feature)

    def generateFeatures(self, att, vals):
        for val in vals:
            self.add_feature(Feature(att, val.strip()))

    def __str__(self):
        extras = ""
        for st in self.semantic_types:
            extras += ''
        return "\n".join(['<SemanticPredicate id="%s">' % (self.id),
                          "\n".join(['\n<feat att="semanticType" val="%s"/>' % (st) for st in self.semantic_types]),
                          "\n".join([str(fe) for fe in self.features]),
                          "\n".join([str(sa) for sa in self.semantic_arguments]),
                          '</SemanticPredicate>'
                          ])


class SemanticArgument:
    def __init__(self, semantic_role, core_type):
        self.semantic_role = semantic_role
        self.core_type = core_type

    def __str__(self):
        return '<SemanticArgument><feat att="semanticRole" val="%s"/><feat att="type" val="%s"/></SemanticArgument>' % (self.semantic_role, self.core_type)


class SemanticLabel:
    """
    Optional subclass of Sense, SemanticPredicate, and SemanticArgument
    to cope with a large variety of lexical-semantic labels.
    """
    def __init__(self, feat_attrs, label="", _type="", quantification=""):
        """Expects a list of feature-attribute tuples."""
        self.feat_attrs = feat_attrs
        self.label = label
        self.type = _type
        self.quantification = quantification

    def add_feature(self, feature, attr):
        self.feat_attrs.append((feature, attr))

    def __str__(self):
        attrs = [i for i in [("label", self.label), ("type", self.type), ("quantification", self.quantification)] if i[1]]
        semantic_attr = '<SemanticLabel'
        for attr, val in attrs:
            semantic_attr += ' %s="%s"' % (attr, val)
        semantic_attr += '>'
        semantic_label = [semantic_attr]
        for feat, val in self.feat_attrs:
            semantic_label.append('<feat att="%s" val="%s"/>' % (feat, val))
        semantic_label.append('</SemanticLabel>')
        return "\n".join(semantic_label)


class PredicativeRepresentation:
    def __init__(self, idref):
        self.idref = idref

    def __str__(self):
        return '<PredicativeRepresentation predicate="%s" correspondences="%s"/>' % (self.idref, self.idref)


class Etymology:
    def __init__(self):
        self.etymons = []

    def add_etymon(self):
        etymon = Etymon()
        self.etymons.append(etymon)
        return etymon

    def __str__(self):
        strs = []
        for i, etymon in enumerate(self.etymons):
            etymon.set_id(str(i))
            strs.append(str(etymon))

        return '<etymology>'+'\n'.join(strs)+'</etymology>'


class Etymon:
    def __init__(self):
        self.forms = []
        self.etymid = ''

    def add_form(self, lang, form, desc=''):
        self.forms.append((lang, form, desc))

    def set_id(self, etymid):
        self.etymid = etymid

    def __str__(self):
        etymon_str = []
        for lang, form, desc in self.forms:
            descxml = '<note>%s</note>' % desc if desc else ''
            etymon_str.append('<form> <orth xml:lang="%s">%s</orth> %s</form>' % (lang, form, descxml))
        return '<etymon id="LE%s">' % self.etymid + '\n'.join(etymon_str) + '</etymon>'


# HELPER FUNCTIONS ------------------------------------------------------------
def escape(s):
    if type(s) != str:
        s = str(s)
    # Avoid double escaping by first unescaping
    return html.escape(html.unescape(s))
    # if type(s) != str:
    #     s = str(s)
    # s = s.replace('&', '&amp;')
    # s = s.replace("'", '&apos;')
    # s = s.replace('<', '&lt;')
    # s = s.replace('>', '&gt;')
    # return s.replace('"', '&quot;')


def xml_to_string(xml, lmfobj):
    """ Converts a valid a xml blob into a string
        Removes namespace definitions from this xml snippet
        but saves the information for later usage
    """

    xml = str(xml)
    ns = re.findall('xmlns:(.*?)="(.*?)"', xml)
    xml = re.sub('(</?)(example|text|e|g)([ />])', r'\1karp:\2\3', xml)
    for name, space in ns:
        lmfobj.namespaces[name] = space
    xml = re.sub('xmlns:.*?=".*?"', '', xml)
    xml = re.sub('ns\d=".*?"', '', xml)
    return xml

    #  ns = re.search('ns0="([^"]*)"',xml)
    #  if ns is not None:
    #      ns = ns.group(1)
    #      xml = re.sub(':ns0="[^"]*"','',xml)
    #      xml = re.sub('ns0',ns,xml)

    #  # the dummy node is added to make it possible to translate xml blobs inculding junk
    #  # at the end, such as 'None'. The junk should be ultimately be removed, but is
    #  # present in eg. konstruktikon
    #  return etree.tostring(list(etree.fromstring('<dummy>%s</dummy>'))[0])
