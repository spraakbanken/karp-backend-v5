# coding:utf-8
import cgi
import logging
""" Convert lexicon entries from json to csv or tsv """


def format_posts(ans, mode, toformat='html'):
    hits = ans.get('hits', {}).get('hits', [])
    func = mode_conv.get(mode, default)
    # ans['objs'] = hits
    # return
    ok, tab = func([hit['_source'] for hit in hits])
    del ans['hits']
    ans['formatted'] = tab


def termswefin(objs):
    logging.debug('starting with: %s' % objs)
    lines = []
    for obj in objs:
        # make one line for every subtype and translation for every entry
        for subtype in obj.get('subtype', ["-"]):
            line = []
            line.append('<strong>%s</strong>' % escape(obj['baselang'].get('form')[0].get('wordform')))
            line.append(escape(obj['baselang'].get('form')[0].get('comment', '')))
            for target in obj.get('targetlang'):
                translations = []
                for tform in target.get('form', []):
                    form = escape(tform.get('wordform', ''))
                    comm = escape(tform.get('comment', ''))
                    comm = ' '+comm if comm else comm
                    translations.append('<em>%s%s</em>' % (form, comm))
            line.append(', '.join(translations))

            for i, ex in enumerate(obj.get('baselang').get('compound', [])):
                try:
                    target = escape(obj.get('targetlang', [{}])[0].get('compound')[i])
                except:
                    target = '-'
                line.append(u'<br/>      %s <em>%s</em>' % (escape(ex), target))

            line.append('<br/>')
            lines.append(' '.join(line))
    return len(objs), ''.join(lines)


def escape(string):
    # Maybe do something smarter
    return cgi.escape(string.strip())


def default(obj, toformat):
    return 0, "no translation available"


mode_conv = {"term-swefin": termswefin}

'''
<p><strong>Svenska</strong> (komm) <em>finska1 (komm), finska2</em><br />      underord <em>översätt</em><br />      underord2 <em>översätt</em></p>
<p><strong>Svenska</strong> (komm) <em>finska1 (komm), finska2</em><br />      underord <em>översätt</em><br />      underord2 <em>översätt</em></p>
'''
