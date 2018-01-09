import copy
import json
# TODO get rid of this
import sys
print sys.path
sys.path.append('/export/htdocs_sbws/ws/karp/v6/')
print sys.path

import src.server.helper.configmanager as configM
import sys
print sys.path


def read_fieldmappings(mode):
    " Open a mode's config file and combine them "
    default_fields = copy.deepcopy(configM.defaultfields)
    # step through the group members if the mode is an aliasmode
    # or use it's own config file if it's a indexmode
    all_fields = {}
    print "create", mode
    for index in configM.searchconfig[mode].get('groups', [mode]):
        try:
            print "read", index
            fields = json.load(open('config/mappings/fieldmappings_'+index+'.json'))
            merge_dict(all_fields, fields)
        except IOError:
            print 'no file for', index

    complement_dict(all_fields, default_fields)
    return all_fields


def print_all(outpath):
    " Find all modes and print their field configs "
    all_mappings = []
    for name in configM.searchconfig.keys():
        conf_str = []
        for key, val in read_fieldmappings(name).items():
            print 'debug', key, val
            if type(val) is dict:
                conf_str.append('"%s": %s'
                                % (key, json.dumps(val)))
            else:
                conf_str.append('"%s": [%s]'
                                % (key, ', '.join('"%s"' % v for v in val)))

        all_mappings.append('\n"%s": {\n  %s\n  }'
                            % (name, ',\n  '.join(conf_str)))

    open(outpath, 'w').write('{\n%s\n}' % ',\n'.join(all_mappings))


def complement_dict(adict, bdict):
    " Adds values from bdict into adict unless the key is already there "
    for key, val in bdict.items():
        if key not in adict:
            adict[key] = val


def merge_dict(adict, bdict):
    " Merges bdict into adict by taking the union of the vaule lists "
    for key, val in bdict.items():
        if key in adict:
            adict[key] = list(set(adict[key]) | set(val))
        else:
            adict[key] = val


if __name__ == "__main__":
    outpath = 'config/fieldmappings.json'
    print_all(outpath)
