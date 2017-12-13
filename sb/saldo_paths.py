# -*- coding: utf-8 -*-
""" 
Script for collection information about sense relations in saldo
Two dictionaries are created, one with all children for each senseid,
and one with the primary parent of all senseids
"""
import xml.etree.ElementTree as etree
import collections
from os.path import isfile

def get_relations(fil):
    if type(fil)==str and not isfile(fil):
        root =  etree.fromstring(fil)
    else:
        root =  etree.parse(fil).getroot()
            
    kids = collections.defaultdict(dict)
    path = collections.defaultdict(dict)
    for elem in root:
        if elem.tag == "Lexicon":
            # Return iterator of all LexicalEntries
            find_kids(elem,kids,path)
    return kids,path


def find_kids(elem,kids,path):
    """ Prints the lexicon with each entry on one line, in json format 
        Before each line an index instruction is added 
    """

    for e in elem:
         if e.tag == "LexicalEntry":
             for sense in e.findall('Sense'):
                 find_SenseRelations(sense, kids, path)

def find_SenseRelations(elem, kids, path):
    """ Converts the Sense. Keeps the senseid and a list of relations
    """
    senseid = elem.attrib.get('id')
    for relation in list(elem):
        if relation.tag=="SenseRelation":
            for k,v in relation.attrib.items():
                if k == "targets": # primary or secondary?
                    target = v
            for e in relation:
                if e.tag=="feat":
                    if e.attrib.get('att','') == "label":
                        lab = e.attrib.get('val')
                        paths = kids.setdefault(target,collections.defaultdict(dict))
                        paths.setdefault(lab,[]).append(senseid)
                        if lab=="primary":
                            path[senseid] = target
                            

def find_path(sense, paths):
    path = [sense]
    while paths[sense]:
        sense = paths[sense]
        path.append(sense)
    return path




