# import copy
import json

from karp5.config import mgr as conf_mgr

# TODO check if file 'config/fieldmappings.json' exist, if not create it.

# def read_fieldmappings(mode):
#     " Open a mode's config file and combine them "
#     default_fields = copy.deepcopy(configM.defaultfields)
#     # step through the group members if the mode is an aliasmode
#     # or use it's own config file if it's a indexmode
#     all_fields = {}
#     print "create", mode
#     for index in conf_mgr.modes[mode].get('groups', [mode]):
#         try:
#             print "read", index
#             fields = json.load(open('config/mappings/fieldmappings_'+index+'.json'))
#             merge_dict(all_fields, fields)
#         except IOError:
#             print 'no file for', index
#
#     complement_dict(all_fields, default_fields)
#     return all_fields


def print_all(outpath):
    " Find all modes and print their field configs "
    with open(outpath, "w") as fp:
        json.dump(conf_mgr.fields, fp, indent=2)


# def complement_dict(adict, bdict):
#     " Adds values from bdict into adict unless the key is already there "
#     for key, val in bdict.items():
#         if key not in adict:
#             adict[key] = val
#
#
# def merge_dict(adict, bdict):
#     " Merges bdict into adict by taking the union of the vaule lists "
#     for key, val in bdict.items():
#         if key in adict:
#             adict[key] = list(set(adict[key]) | set(val))
#         else:
#             adict[key] = val
#
#
# if __name__ == "__main__":
#     outpath = 'config/fieldmappings.json'
#     print_all(outpath)
