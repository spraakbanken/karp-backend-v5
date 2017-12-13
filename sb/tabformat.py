# coding:utf-8
import logging

""" Convert lexicon entries from json to csv or tsv """


def format_posts(ans, mode, toformat='tab'):
    hits = ans.get('hits', {}).get('hits', [])
    func = mode_conv.get(mode, default)
    # ans['objs'] = hits
    # return
    ok, tab = func([hit['_source'] for hit in hits], toformat)
    del ans['hits']
    ans['formatted'] = tab


def termswefin(objs, toformat):
    tab = '\t' if toformat in ['tab', 'tsv'] else ','
    logging.debug('starting with: %s' % objs)
    lines = []
    header = ['Sv', '', 'Fi', '', u'sakområde', 'status', 'intern kommentar',
              u'senast ändrad', u'senast ändrad av', 'underord']
    lines.append(tab.join(header))
    for obj in objs:
        # make one line for every subtype and translation for every entry
        for subtype in obj.get('subtype', ["-"]):
            for target in obj.get('targetlang'):
                for tform in target.get('form', []):
                    line = []
                    line.append(escape(obj['baselang'].get('form')[0].get('wordform'), tab))
                    line.append(escape(obj['baselang'].get('form')[0].get('comment', '""'), tab))
                    line.append(escape(tform.get('wordform'), tab))
                    line.append(escape(tform.get('comment', '""'), tab))
                    line.append(escape(subtype, tab))
                    line.append(escape(obj.get('termstatus', '""'), tab))
                    line.append(escape(obj.get('terminternalcomment', '""'), tab))
                    line.append(escape(obj.get('lastmodified', ''), tab))
                    line.append(escape(obj.get('lastmodifiedBy', ''), tab))
                    # just list the swedish/sourcelang compounds
                    for ex in obj.get('baselang').get('compound', []):
                        line.append(escape(ex, tab))
                    lines.append(tab.join(line))
    return len(objs), '\n'.join(lines).encode('utf8')


def escape(string, tab):
    # comma in csv format is handled by enclosing the string in quotes
    if tab == ',' and tab in string:
        string = '"%s"' % string
    return string


def default(obj, toformat):
    return 0, "no translation available"


mode_conv = {"term-swefin": termswefin}
