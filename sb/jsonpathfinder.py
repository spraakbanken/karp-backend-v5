import json
import sys


def find_path(obj):
    paths = {}
    if type(obj) is list:
        paths['.'] = set()
        for o in obj:
            paths['.'].update(find_path(o))
    elif type(obj) is dict:
        for key, val in obj.items():
            if key not in paths:
                paths[key] = set()
            if type(val) is list:
                for v in val:
                   if type(v) is dict:
                       paths[key].update(find_path(v))
            if type(val) is dict:
                paths[key].update(find_path(val))

    return set(sum([show(k,v) for k,v in paths.items()],[]))

def show(k,v):
    if not v:
        return [k]
    if type(v) is set:
        return ['%s.%s' % (k,val) for val in v]
    return ['%s.%s' % (k,v)]

if __name__=="__main__":
    print 'hej'
    inp = sys.stdin.read()
    obj = json.loads(inp)
    paths = find_path(obj)
    print paths
