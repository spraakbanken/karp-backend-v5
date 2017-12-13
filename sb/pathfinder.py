#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import xml.etree.cElementTree as etree

xmlstring = sys.stdin.read()

root = etree.XML(xmlstring)

bag_of_paths = set()

def print_path_of_elems(elem, elem_path=""):
    global bag_of_paths
    for child in elem:
        if not child.getchildren():
            extra = ""
            if child.tag == "feat":
                extra = "_" + child.get("att")
            bag_of_paths.add("%s/%s%s" % (elem_path, child.tag, extra))
        else:
            print_path_of_elems(child, "%s/%s" % (elem_path, child.tag))

print_path_of_elems(root, root.tag)
print "\n".join(bag_of_paths)