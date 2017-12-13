# -*- encoding:UTF-8 -*-
import xml.etree.ElementTree as ET
import lxml.etree as lET
import sys


# konstruktikon
k_entries_to_remove = [("Lexicon/LexicalEntry",
                        "Sense/feat[@att='entry_status']",
                        lambda x: x.attrib['val'] == 'Suggestion')]

k_entries_path = "Lexicon/LexicalEntry"
k_to_remove = ["Sense/feat[@att='internal_comment']",
               "Sense/feat[@att='createdBy']",
               "Sense/feat[@att='entry_status']"
               ]


# swefn
s_entries_to_remove = []
# LexicalResource/Lexicon/LexicalEntry/Sense/feat_entry_status => ta bort hela
# om det är Development?

s_entries_path = "Lexicon/LexicalEntry"
s_to_remove = ["Sense/feat[@att='internal_comment']",
               "Sense/feat[@att='createdBy']",
               "Sense/feat[@att='suggestionForLU']",
               "Sense/feat[@att='createdDate']",
               ]
# "Sense/feat[@att='entry_status']"
# "Sense/feat[@att='problematicLU']",
# "Lexicon/LexicalEntry/Sense/feat_comment"]
#        => verkar användas ungefär som internal_comment

hellqvist_entries_to_remove = []
hellqvist_entries_path = "Lexicon/LexicalEntry"
hellqvist_to_remove = ["feat[@att='lastmodifiedBy']",
                       "feat[@att='lastmodified']",
                       "Sense/feat[@att='hellqvistStatus']"
                      ]


lexdata = {'konstruktikon': (k_entries_path, k_entries_to_remove, k_to_remove),
           'konstruktikon-rus': (k_entries_path, k_entries_to_remove, k_to_remove),
           'konstruktikon-multi': (k_entries_path, k_entries_to_remove, k_to_remove),
           'swefn': (s_entries_path, s_entries_to_remove, s_to_remove),
           'langfn': (s_entries_path, s_entries_to_remove, s_to_remove),
           'hellqvist': (hellqvist_entries_path, hellqvist_entries_to_remove, hellqvist_to_remove),
           'blingbring': (hellqvist_entries_path, hellqvist_entries_to_remove, hellqvist_to_remove)
           }


def clean_xml(name, fil):
    # The actual clean up
    root, comments = parse_xmlns(fil)
    entries_path, entries_to_remove, to_remove = lexdata[name]

    for path, check, condition in entries_to_remove:
        for elem in root.findall('.//' + entries_path):
            checkelem = elem.find(check)
            if checkelem is not None and condition(checkelem):
                # print >> sys.stderr, 'remove', elem.tag, elem.attrib.items()
                parent = root.find('.//' + path + '/..')
                parent.remove(elem)

    for parent in root.findall('.//' + entries_path):
        for path in to_remove:
            for elem in parent.findall(path):
                # print >> sys.stderr, 'remove', elem.tag, elem.attrib.items()
                parent.find(path + '/..').remove(elem)

    write_xmlns(root, comments)


# Below: Parsing and printing trees with the original namespaces kept
# Copied from http://effbot.org/zone/element-namespaces.htm
def parse_xmlns(file):

    # ElementTree handles namespaces well
    events = "start", "start-ns"
    root = None
    ns_map = []

    for event, elem in ET.iterparse(file, events):

        if event == "start-ns":
            ns_map.append(elem)

        elif event == "start":
            if root is None:
                root = elem
            for prefix, uri in ns_map:
                elem.set("xmlns:" + prefix, uri)
            ns_map = []

    # ...but can not read comments. Therefore parse them with lxml.
    # top level comments may be <-- $Date $ -->
    # (NB: hakish solution, but works for our purposes)
    events = "comment",
    comments = []
    for event, elem in lET.iterparse(file, events):

        if event == "comment":
            comments.append(elem)

    return root, comments


def fixup_xmlns(elem, maps=None):

    if maps is None:
        maps = [{}]

    # check for local overrides
    xmlns = {}
    for key, value in elem.items():
        if key[:6] == "xmlns:":
            xmlns[value] = key[6:]
    if xmlns:
        uri_map = maps[-1].copy()
        uri_map.update(xmlns)
    else:
        uri_map = maps[-1]

    # fixup this element
    fixup_element_prefixes(elem, uri_map, {})

    # process elements
    maps.append(uri_map)
    for elem in elem:
        fixup_xmlns(elem, maps)
    maps.pop()


def fixup_element_prefixes(elem, uri_map, memo):
    def fixup(name):
        try:
            return memo[name]
        except KeyError:
            if name[0] != "{":
                return
            uri, tag = name[1:].split("}")
            if uri in uri_map:
                new_name = uri_map[uri] + ":" + tag
                memo[name] = new_name
                return new_name
    # fix element name

    name = fixup(elem.tag)
    if name:
        elem.tag = name
    # fix attribute names
    for key, value in elem.items():
        name = fixup(key)
        if name:
            elem.set(name, value)
            del elem.attrib[key]


def write_xmlns(elem, comments):

    if not ET.iselement(elem):
        elem = elem.getroot()

    fixup_xmlns(elem)

    print '\n'.join([lET.tostring(c) for c in comments])
    print ET.tostring(elem, encoding='UTF-8')


if __name__ == '__main__':
    clean_xml(sys.argv[1], sys.argv[2])
