import csv
import json
import StringIO
import sys

def tocsv(objs, source=''):
    flat = [flattenjson(obj, '.') for obj in objs]
    print flat
    columns = map(lambda x: x.keys(), flat)
    columns = reduce(lambda x,y: x+y, columns)
    columns = filter(lambda x: x.startswith(source), columns)
    if source:
        columns = map(lambda x: x.split('.', 1)[-1], columns)
    columns = list(set(columns))
    print 'columns', columns
    out_file = StringIO.StringIO()
    csv_w = csv.writer(out_file, delimiter='\t', quotechar='\\')
    csv_w.writerow(columns)

    for i_r in flat:
        csv_w.writerow(map(lambda x: i_r.get(source+x, ""), columns))
    return out_file.getvalue()


def flattenjson(b, delim):
    val = {}
    for i in b.keys():
        if isinstance(b[i], dict):
            get = flattenjson(b[i], delim)
            for j in get.keys():
                val['%s%s%s' % (i,delim,j)] = get[j]
        elif isinstance(b[i], list):
            inner = []
            for item in b[i]:
                if isinstance(item, dict):
                    inner.append(flattenjson(item, delim))
            innerkeys = set(sum(map(lambda x: x.keys(), inner), []))
            for key in innerkeys:
                innerval = filter(lambda x: x is not None, map(lambda x: x.get(key), inner))
                if len(innerval) < 2:
                    innerval = innerval[0]
                print 'add',innerval
                val['%s%s%s' % (i, delim, key)] = innerval
        else:
            val[i] = b[i]

    return val


if __name__ == "__main__":
    objs = sys.stdin.read()
    print tocsv(json.loads(objs)) #, 'test.csv')
