import json
import logging
import sb.converter.htmlconv as htmlconv
import sb.converter.tabformat as tabconv
import src.server.errorhandler as eh
import src.server.helper.configmanager as configM


#def format_posts(ans, es, mode, index, toformat):
def format(ans, es, mode, index, toformat):
    tabmodes = tabconv.mode_conv
    htmlmodes = htmlconv.mode_conv
    logging.debug('\n\nhello its format\n\n')
    if toformat in ['tab', 'csv', 'tsv'] and mode in tabmodes:
        tabconv.format_posts(ans, mode, toformat)

    if toformat in ['html'] and mode in htmlmodes:
        htmlconv.format_posts(ans, mode)

    if toformat in ['lmf', 'xml']:
        # TODO in most cases, mode is not enough information, we will also need
        # lexicon. either add function in parsejson which looks at each entry
        # and its lexicon or go through the data list here  make multiple calls
        # here (one for each lexicon)
        # TODO 'ans' contains hits.hits etc.
        try:
            hits = [hit['_source'] for hit in ans.get('hits', {}).get('hits', [])]
            lmf, err = call_lmfformat(mode, hits)
            logging.debug('lmf %s' % lmf)
            del ans['hits']
            ans['formatted'] = lmf
        except Exception as e:
            logging.exception(e)
            raise eh.KarpGeneralError("Cannot convert lexicon %s to xml\n" % mode)

    raise eh.KarpGeneralError("Cannot format mode %s to format %s" % (mode, toformat))


# export_posts
def exportformat(ans, lexicon, mode, toformat):
    if toformat in ['lmf', 'xml']:
        try:
            lmf, err = call_lmfformat(lexicon, ans)
            logging.debug('err %s' % err)
            return lmf, err

        except Exception as e:  # catch *all* exceptions
            # TODO only catch relevant exceptions
            logging.exception(e)
            raise eh.KarpGeneralError("Cannot convert lexicon to xml\n", "")


def call_lmfformat(lexicon, ans):
    # return lmf, err
    from subprocess import Popen, PIPE
    # Coversion must be run as python3.
    # Run in virtualenv with pycountry
    p_dir = configM.setupconfig['absolute_path']
    venv3 = 'venv3/bin/activate'
    parsejson = 'sb/converter/parsejson.py'
    py_enc = 'PYTHONIOENCODING=utf-8:surrogateescape'
    command = 'cd %s; source %s; %s python3 %s --mklmf %s; deactivate'\
              % (p_dir, venv3, py_enc, parsejson, lexicon)
    logging.debug('command %s' % command)
    p = Popen([command], shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    return p.communicate(input=json.dumps(ans))
