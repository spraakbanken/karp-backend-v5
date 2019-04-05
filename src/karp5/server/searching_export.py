# -*- coding: utf-8 -*-
import copy
import elasticsearch
from flask import request, jsonify, Response, stream_with_context, copy_current_request_context
from itertools import chain
from json import loads, dumps
import re

import karp5.dbhandler.dbhandler as db
from karp5 import errors
from karp5.server.auth import validate_user
from karp5.config import mgr as conf_mgr
import karp5.server.helper.helpers as helpers

from karp5.server.translator import parser
from karp5.server.translator import parsererror as PErr

from gevent.threadpool import ThreadPool
from gevent.queue import Queue, Empty
import functools
import sys
import time

import logging
""" Methods for querying the data base """

_logger = logging.getLogger('karp5')


def query(page=0):
    try:
        ans = requestquery(page=page)
        return jsonify(ans)

    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except Exception as e:  # catch *all* exceptions and show for user
        _logger.exception(e)
        raise errors.KarpGeneralError(str(e), user_msg=str(e),
                                  query=request.query_string)


def requestquery(page=0):
    """ The Function for querying our database """
    # page is assumed to be 0 indexed here
    auth, permitted = validate_user(mode="read")
    try:
        # default values
        default = {'size': 25, 'page': page, 'version': 'true'}
        settings = parser.make_settings(permitted, default)
        elasticq = parser.parse(settings)
    except PErr.QueryError as e:
        _logger.exception(e)
        raise errors.KarpQueryError('Parse error', debug_msg=e.message,
                                query=request.query_string)
    except PErr.AuthenticationError as e:
        _logger.exception(e)
        msg = e.message
        raise errors.KarpAuthenticationError(msg)
    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except Exception as e:  # catch *all* exceptions
        _logger.exception(e)
        raise errors.KarpQueryError("Could not parse data", debug_msg=e,
                                query=request.query_string)
    mode = settings['mode']
    sort = sortorder(settings, mode, settings.get('query_command', ''))
    start = settings['start'] if 'start' in settings\
                              else settings['page'] * settings['size']

    # size = min(settings['size'], setupconf.max_page)
    size = settings['size']
    index, typ = conf_mgr.get_mode_index(mode)
    exclude = conf_mgr.searchfield(mode, 'secret_fields') if not auth else []
    ans = parser.adapt_query(size, start, conf_mgr.elastic(mode=mode), loads(elasticq),
                             {'size': size, 'sort': sort, 'from_': start,
                              'index': index,
                              '_source_exclude': exclude,
                              'version': settings['version'],
                              'search_type': settings.get('search_type', None)})

    if settings.get('highlight', False):
        clean_highlight(ans)

    if settings.get('format') or settings.get('export'):
        formatmethod = 'format' if 'format' in settings else 'export'
        toformat = settings.get(formatmethod)
        msg = 'Unkown %s %s for mode %s' % (formatmethod, toformat, mode)
        format_posts = conf_mgr.extra_src(mode, formatmethod, helpers.notdefined(msg))
        format_posts(ans, conf_mgr.elastic(mode=mode), mode, index, toformat)

    return ans


def sortorder(settings, mode, querycommand):
    if not settings.get('sort', ''):
        if querycommand == "simple":
            # default: group by lexicon, then sort by score
            sort = conf_mgr.searchfield(mode, 'sort_by')
        else:
            # default for extended query: exclude _score
            sort = [field for field in conf_mgr.searchfield(mode, 'sort_by')
                    if field != "_score"]
    else:
        sort = conf_mgr.searchfield(mode, 'head_sort_field') + settings['sort']

    return sort


def querycount(page=0):
    # TODO error if buckets is used here
    # TODO validate_user is also done once in requestquery
    # but since we need the permitted dict, it is called
    # here as well
    auth, permitted = validate_user(mode="read")
    try:
        # TODO buckets should be gathered from some config
        stat_size = request.args.get('statsize', conf_mgr.app_config.MAX_PAGE)
        default = {"buckets": ['lexiconOrder', 'lexiconName'],
                   "size": stat_size}
        settings = parser.make_settings(permitted, default)
        q_ans = requestquery(page=page)

        # raise the size for the statistics call
        count_elasticq, more = parser.statistics(settings,
                                                 order={"lexiconOrder":
                                                        ("_key", "asc")},
                                                 show_missing=False,
                                                 force_size=stat_size)
        mode = settings['mode']
        es = conf_mgr.elastic(mode=mode)
        index, typ = conf_mgr.get_mode_index(mode)
        _logger.debug('Will ask %s' % count_elasticq)
        # TODO does search_type=count work with the new es version?
        # if not, use query_then_fetch, size=0
        count_ans = es.search(index=index,
                              body=loads(count_elasticq),
                              search_type="query_then_fetch",
                              # raise the size for the statistics call
                              size=0  # stat_size
                              )
        distribution = count_ans['aggregations']['q_statistics']['lexiconOrder']['buckets']
    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise

    except (elasticsearch.RequestError, elasticsearch.TransportError) as e:
        _logger.exception(e)
        raise errors.KarpElasticSearchError("ElasticSearch failure. Message: %s.\n" % e)

    except Exception as e:  # catch *all* exceptions
        # Remember that 'buckets' is not allowed here! %s"
        _logger.exception(e)
        raise errors.KarpQueryError("Could not parse data", debug_msg=e,
                                query=request.query_string)
    return jsonify({'query': q_ans, 'distribution': distribution})


def test():
    auth, permitted = validate_user(mode="read")
    try:
        # default
        settings = parser.make_settings(permitted, {'size': 25, 'page': 0})
        elasticq = parser.parse(settings)
    except PErr.QueryError as e:
        raise errors.KarpQueryError("Parse error", debug_msg=e, query=request.query_string)
    return jsonify({'elastic_json_query': loads(elasticq)})


def explain():
    auth, permitted = validate_user(mode="read")
    try:
        # default
        settings = parser.make_settings(permitted, {'size': 25, 'page': 0})
        elasticq = parser.parse(settings)
    except PErr.QueryError as e:
        raise errors.KarpQueryError("Parse error", debug_msg=e, query=request.query_string)
    es = conf_mgr.elastic(mode=settings['mode'])
    index, typ = conf_mgr.get_mode_index(settings['mode'])
    ex_ans = es.indices.validate_query(index=index,
                                       body=loads(elasticq), explain=True)
    q_ans = requestquery(page=0)
    return jsonify({'elastic_json_query': loads(elasticq), 'ans': q_ans,
                    'explain': ex_ans})


def minientry():
    """ Returns the counts and stats for the query """
    max_page = conf_mgr.app_config.MINIENTRY_PAGE
    auth, permitted = validate_user(mode="read")
    try:
        mode = parser.get_mode()
        default = {'show': conf_mgr.searchfield(mode, 'minientry_fields'),
                   'size': 25}
        settings = parser.make_settings(permitted, default)
        elasticq = parser.parse(settings)
        show = settings['show']
        if not auth:
            # show = show - exclude
            exclude = conf_mgr.searchfield(mode, 'secret_fields')
            show = list(set(show).difference(exclude))

        sort = sortorder(settings, mode, settings.get('query_command', ''))
        start = settings['start'] if 'start' in settings else 0
        es = conf_mgr.elastic(mode=settings['mode'])
        index, typ = conf_mgr.get_mode_index(settings['mode'])
        ans = parser.adapt_query(settings['size'], start, es, loads(elasticq),
                                 {'index': index, '_source': show,
                                  'from_': start, 'sort': sort,
                                  'size': min(settings['size'], max_page),
                                  'search_type': 'dfs_query_then_fetch'}
                                 )
        if settings.get('highlight', False):
            clean_highlight(ans)

        return jsonify(ans)
    except PErr.AuthenticationError as e:
        _logger.exception(e)
        msg = e.message
        raise errors.KarpAuthenticationError(msg)
    except PErr.QueryError as e:
        raise errors.KarpQueryError("Parse error, %s" % e.message, debug_msg=e,
                                query=request.query_string)
    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except Exception as e:  # catch *all* exceptions
        _logger.exception(e)
        raise errors.KarpGeneralError("Unknown error", debug_msg=e, query=query)


def random():
    auth, permitted = validate_user(mode="read")
    try:
        mode = parser.get_mode()
        default = {"show": conf_mgr.searchfield(mode, 'minientry_fields'),
                   "size": 1}
        settings = parser.make_settings(permitted, default)
        elasticq = parser.random(settings)
        es = conf_mgr.elastic(mode=mode)
        index, typ = conf_mgr.get_mode_index(mode)
        es_q = {'index': index, 'body': loads(elasticq),
                'size': settings['size']}
        if settings['show']:
            show = settings['show']
            if not auth:
                # show = show - exclude
                exclude = conf_mgr.searchfield(mode, 'secret_fields')
                show = list(set(show).difference(exclude))
            es_q['_source'] = show

        ans = es.search(**es_q)
        return jsonify(ans)
    except PErr.AuthenticationError as e:
        _logger.exception(e)
        msg = e.message
        raise errors.KarpAuthenticationError(msg)
    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except Exception as e:  # catch *all* exceptions
        _logger.exception(e)
        raise errors.KarpGeneralError("Unknown error", debug_msg=e, query=request.query_string)


def statistics():
    """ Returns the counts and stats for the query """
    auth, permitted = validate_user(mode="read")
    try:
        mode = parser.get_mode()
        default = {"buckets": conf_mgr.searchfield(mode, 'statistics_buckets'),
                   "size": 100, "cardinality": False}
        settings = parser.make_settings(permitted, default)
        exclude = [] if auth else conf_mgr.searchfield(mode, 'secret_fields')

        elasticq, more = parser.statistics(settings, exclude=exclude)
        es = conf_mgr.elastic(mode=settings['mode'])
        index, typ = conf_mgr.get_mode_index(settings['mode'])
        is_more = check_bucketsize(more, settings, index, es)

        # TODO allow more than 100 000 hits here?
        _logger.debug('stat body %s' % elasticq)
        ans = es.search(index=index, body=loads(elasticq),
                        search_type="query_then_fetch", size=0)
        ans["is_more"] = is_more
        return jsonify(ans)
    except PErr.AuthenticationError as e:
        _logger.exception(e)
        msg = e.message
        raise errors.KarpAuthenticationError(msg)
    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except Exception as e:  # catch *all* exceptions
        _logger.exception(e)
        raise errors.KarpGeneralError("Unknown error", debug_msg=e, query=request.query_string)


def statlist():
    # TODO add is_more here (as above)
    """ Returns the counts and stats for the query """
    auth, permitted = validate_user(mode="read")
    try:
        mode = parser.get_mode()
        _logger.debug('mode is %s' % mode)
        default = {"buckets": conf_mgr.searchfield(mode, 'statistics_buckets'),
                   "size": 100, "cardinality": False}
        settings = parser.make_settings(permitted, default)

        exclude = [] if auth else conf_mgr.searchfield(mode, 'secret_fields')
        elasticq, more = parser.statistics(settings, exclude=exclude,
                                           prefix='STAT_')
        es = conf_mgr.elastic(mode=settings['mode'])
        index, typ = conf_mgr.get_mode_index(settings['mode'])
        is_more = check_bucketsize(more, settings["size"], index, es)
        # TODO allow more than 100 000 hits here?
        size = settings['size']
        ans = es.search(index=index, body=loads(elasticq),
                        search_type="query_then_fetch", size=0)
        tables = []
        for key, val in ans['aggregations']['q_statistics'].items():
            if key.startswith('STAT_'):
                tables.extend(generate_table(val, []))
        # the length of tables might be longer than size, so truncate it
        # generating shorter tables is not faster than generating all of it
        # and then truncating
        if size:
            tables = tables[:size]
        return jsonify({"stat_table": tables, "is_more": is_more})

    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except PErr.AuthenticationError as e:
        _logger.exception(e)
        msg = e.message
        raise errors.KarpAuthenticationError(msg)
    except Exception as e:  # catch *all* exceptions
        # raise
        _logger.exception(e)
        raise errors.KarpGeneralError("Unknown error", debug_msg=e, query=request.query_string)


def check_bucketsize(bucket_sizes, size, index, es):
    is_more = {}
    for sizebucket, bucketname in bucket_sizes:
        countans = es.search(index=index, body=loads(sizebucket),
                             size=0,
                             search_type="query_then_fetch")
        _logger.debug('countans %s' % countans)
        bucketsize = countans['aggregations']['more']['value']
        _logger.debug('size %s, type %s' % (bucketsize, type(bucketsize)))
        if int(bucketsize) > size:
            is_more[bucketname] = int(bucketsize)
    return is_more


def generate_table(dictionary, table):
    name = dictionary.get('key', '')
    end = True
    tables = []
    for key, val in dictionary.items():
        if key.startswith('STAT_'):
            end = False
            tables.extend(generate_table(val, table + [name]))
        if key == 'buckets':
            end = False
            for bucket in val:
                tables.extend(generate_table(bucket, table))
    if end:
        count = dictionary.get('doc_count', 0)
        if count:
            tables.append(table + [name, count])

    return tables


def formatpost():
    """ Formats the posted data into wanted format
        The data should be a list
        Currently only working for saol
    """
    # get and parse data
    request.get_data()
    data = request.data
    try:
        data = loads(data)
    except ValueError as e:
        raise errors.KarpParsingError(str(e))

    # set all allowed lexicons (to avoid authentication exception
    auth, permitted = validate_user(mode="read")
    # find the wanted format
    settings = parser.make_settings(permitted, {'size': 25})
    parser.parse_extra(settings)
    to_format = settings.get('format', '')
    mode = parser.get_mode()
    _logger.debug('mode "%s"' % mode)
    index, typ = conf_mgr.get_mode_index(mode)

    if to_format:
        if type(data) != list:
            data = [data]
        errmsg = 'Unkown format %s for mode %s' % (settings['format'], mode)
        format_list = conf_mgr.extra_src(mode, 'format_list', helpers.notdefined(errmsg))
        ok, html = format_list(data, conf_mgr.elastic(mode=mode), settings['format'], index)
        return jsonify({'all': len(data), 'ok': ok, 'data': html})

    else:
        raise errors.KarpQueryError('Unkown format %s' % to_format)


def autocomplete():
    """ Returns lemgrams matching the query text.
        Each mode specifies in the configs which fields that should be
        considered.
        The parameter 'q' or 'query' is used when only one word form is to be
        processed.
        The parameter 'multi' is used when multiple word forms should be
        processed.
        The format of result depends on which flag that is set.
    """
    auth, permitted = validate_user(mode="read")
    #query = request.query_string
    try:
        settings = parser.make_settings(permitted, {'size': 1000})
        mode = parser.get_mode()
        p_extra = parser.parse_extra(settings)
        if 'q' in request.args or 'query' in request.args:
            qs = [request.args.get('q', '') or request.args.get('query', '')]
            _logger.debug('qs is %s' % qs)
            multi = False
        else:
            # check if there are multiple words forms to complete
            qs = settings.get('multi', [])
            _logger.debug('qs %s' % qs)
            multi = True

        # use utf8, escape '"'
        qs = [re.sub('"', '\\"', q) for q in qs]

        headboost = conf_mgr.searchfield(mode, 'boosts')[0]
        res = {}
        ans = {}
        # if multi is not true, only one iteration of this loop will be done
        for q in qs:
            boost = '''{"term": {"%s": {"boost" : "500", "value": "%s"}}}''' % (headboost, q)

            autocompleteq = conf_mgr.extra_src(mode, 'autocomplete', autocompletequery)
            exp = autocompleteq(mode, boost, q)
            autocomplete_field = conf_mgr.searchonefield(mode, 'autocomplete_field')
            autocomplete_fields = conf_mgr.searchfield(mode, 'autocomplete_field')
            fields = '"exists": {"field" : "%s"}' % autocomplete_field
            # last argument is the 'fields' used for highlightning
            # TODO use filter?
            elasticq = parser.search([exp, fields] + p_extra, [], '', usefilter=True)
            _logger.debug('Will send %s' % elasticq)

            es = conf_mgr.elastic(mode=mode)
            _logger.debug('_source: %s' % autocomplete_field)
            _logger.debug(elasticq)
            index, typ = conf_mgr.get_mode_index(mode)
            ans = parser.adapt_query(settings['size'], 0, es, loads(elasticq),
                                     {'size': settings['size'], 'index': index,
                                      '_source': autocomplete_fields}
                                     )
            # save the results for multi
            res[q] = ans
        if multi:
            return jsonify(res)
        else:
            # single querys: only return the latest answer
            return jsonify(ans)
    except PErr.AuthenticationError as e:
        _logger.exception(e)
        msg = e.message
        raise errors.KarpAuthenticationError(msg)
    except errors.KarpException as e:  # pass on karp exceptions
        _logger.exception(e)
        raise
    except Exception as e:  # catch *all* exceptions
        _logger.exception(e)
        raise errors.KarpGeneralError("Unknown error", debug_msg=e, query=request.query_string)


# standard autocomplete
def autocompletequery(mode, boost, q):
    """ Constructs an autocompletion query, searching for lemgrams starting
        with 'text'
        Returns a query object to be sent to elastic search
    """
    # other modes: don't care about msd
    look_in = [boost]
    for boost_field in conf_mgr.searchfield(mode, 'boosts'):
        look_in.append('{"match_phrase" : {"%s" : "%s"}}' % (boost_field, q))

    exp = '''"bool" : {"should" :
             [%s]}''' % (','.join(look_in))

    return exp


def clean_highlight(ans):
    stop_offset = 9  # The number of extra tokens added by the <em> tags
    for n, hit in enumerate(ans.get('hits', {}).get('hits', [])):
        # _logger.debug('CLEAN hit %s\n\n\n' % hit)
        for field, texts in hit.get('highlight', {}).items():
            # _logger.debug('CLEAN texts %s: %s' % (field, texts))
            if field == 'lexiconName':
                del ans['hits']['hits'][n]['highlight'][field]
            else:
                newtexts = chain(*[re.finditer('<em>(.*?)</em>', t) for t in texts])
                spans = []
                for new in newtexts:
                    spans.append((new.group(1), new.span()[0], new.span()[1] - stop_offset))
                ans['hits']['hits'][n]['highlight'][field] = spans
    ans['hits']['highlight'] = 'ON'


def lexiconorder():
    orderlist = {}
    for name, val in conf_mgr.lexicons.items():
        orderlist[name] = val.get('order', '-1')
    return jsonify(orderlist)


def modeinfo(mode):
    return jsonify(conf_mgr.fields.get(mode, {}))


def lexiconinfo(lexicon):
    return jsonify(conf_mgr.fields.get(conf_mgr.get_lexicon_mode(lexicon), {}))


# For debugging
def testquery():
    """ Returns the query expressed in elastics search api """
    auth, permitted = validate_user(mode="read")
    try:
        from translator import parser
        # default
        settings = parser.make_settings(permitted, {'size': 25, 'page': 0})
        elasticq = parser.parse(settings)
        mode = settings['mode']
        if not settings.get('sort', ''):
            # default: group by lexicon, then sort by score
            sort = conf_mgr.searchfield(mode, 'sort_by')
        else:
            sort = settings['sort']
        start = settings['start'] if 'start' in settings\
                                  else settings['page'] * settings['size']
        elasticq = parser.parse()
        return elasticq + dumps({'sort': sort, '_from': start,
                                 'size': settings['size'],
                                 'version': 'true'})
    except Exception as e:  # catch *all* exceptions
        # TODO only catch relevant exceptions
        _logger.exception(e)
        raise errors.KarpGeneralError(e, request.query_string)


def get_context(lexicon):
    """ Find and return the alphabetically (or similar, as specified for the
    lexicon) context of a word/entry.
    """
    auth, permitted = validate_user(mode="read")
    if lexicon not in permitted:
        raise errors.KarpAuthenticationError('You are not allowed to search the '
                                         'lexicon %s' % lexicon)
    # make default settings
    settings = parser.make_settings(permitted, {"size": 10, "resource": lexicon})
    # parse parameter settings
    parser.parse_extra(settings)

    # set searching configurations
    mode = conf_mgr.get_lexicon_mode(lexicon)
    settings['mode'] = mode
    es = conf_mgr.elastic(mode=mode)
    index, typ = conf_mgr.get_mode_index(mode)

    # get the sort_by list (eg. ['baseform.sort', 'lemmaid.search'])
    # leave out lexiconOrder and _score
    sortfieldnames = [field for field in conf_mgr.searchconf(mode, 'sort_by')
                      if field not in ['_score', 'lexiconOrder']]
    # get the sort field paths (eg. ['FormRep.baseform.raw', 'lemmaid.raw'])
    # Used for sorting.
    sortfield = sum([conf_mgr.lookup_multiple(f, mode) for f in sortfieldnames], [])
    # get the field name of the head sort field. Used for searching
    sortfieldname = sortfieldnames[0]

    # find the center entry (by its id)
    if 'center' in settings:
        center_id = settings['center']
        lexstart = es.search(index=index, doc_type=typ, size=1,
                             body={"query": {"term": {"_id": center_id}}},
                             sort=['%s:asc' % f for f in sortfield])
    # if no center id is given, pick the first entry of the lexicon
    else:
        exps = []
        parser.parse_ext('and|resource|equals|%s' % lexicon, exps, [], mode)
        center_q = parser.search(exps, [], [], usefilter=True, constant_score=False)
        lexstart = es.search(index=index, doc_type=typ, size=1, body=center_q,
                             sort=['%s:asc' % f for f in sortfield])
        center_id = lexstart['hits']['hits'][0]['_id']

        # lexstart = es.search(index=index, doc_type=typ, size=1,
        #                      sort=['%s:asc' % f for f in sortfield])
        # center_id = lexstart['hits']['hits'][0]['_id']

    if not lexstart['hits']['hits']:
        _logger.error('No center found %s, %s' % (center_id, lexstart))
        raise errors.KarpElasticSearchError("Could not find entry %s" % center_id)

    centerentry = lexstart['hits']['hits'][0]
    _logger.debug('center %s, %s' % (centerentry, centerentry['_id']))
    origentry_sort = [key for key in centerentry['sort'] if key is not None][0]
    # TODO what to do if the sort key is not in the lexicon? as below?
    # origentry_sort = centerentry['sort'][0]
    sortvalue = control_escape(origentry_sort)
    _logger.debug(u'Orig entry escaped key %s' % sortvalue)

    # Construct queries to ES
    exps = []
    # the query string from the user
    querystring = settings.get('q', '').decode('utf8')
    parser.parse_ext('and|resource|equals|%s' % lexicon, exps, [], mode)
    if querystring:
        if querystring.startswith('simple'):
            querystring = 'and|anything|equals|%s' % querystring.split('|')[-1]
        else:
            querystring = re.sub('extended\|\|', '', querystring)
        parser.parse_ext(querystring, exps, [], mode)

    preexps = copy.deepcopy(exps)  # deep copy for the pre-query
    hits_post = get_pre_post(exps, center_id, sortfield, sortfieldname,
                             sortvalue, origentry_sort, mode, settings,
                             es, index, place='post')
    hits_pre = get_pre_post(preexps, center_id, sortfield, sortfieldname,
                            sortvalue, origentry_sort, mode, settings,
                            es, index, place='pre')
    return jsonify({"pre": hits_pre[:settings['size']],
                    "post": hits_post[:settings['size']],
                    "center": centerentry})


def get_pre_post(exps, center_id, sortfield, sortfieldname, sortvalue,
                 origentry_sort, mode, settings, es, index, place='post'):
    op = {'post': {'op': 'gte', 'sort': 'asc'},
          'pre': {'op': 'lte', 'sort': 'desc'}}
    parser.parse_ext('and|%s|%s|%s' % (sortfieldname, op[place]['op'], sortvalue),
                     exps, [], mode)
    elasticq_q = parser.search(exps, [], [], usefilter=True, constant_score=False)

    # +1 to compensate for the word itself being in the context
    size = settings['size']+1
    show = conf_mgr.searchfield(mode, 'minientry_fields')
    # TODO size*3 (magic number) because many entries may have the same sort
    # value (eg homographs in saol)
    ans = parser.adapt_query(size*3, 0, es, elasticq_q,
                             {'size': size*3, 'from_': 0,
                              'sort': ['%s:%s' % (f, op[place]['sort']) for f in sortfield],
                              'index': index,
                              '_source': show})

    hits = ans.get('hits', {}).get('hits', [])
    return go_to_sortkey(hits, origentry_sort, center_id)


def go_to_sortkey(hits, sort, center_id):
    """ Step through the lists until the center entry is passed
        The center is at the beginning of the list, or after its homonymns
        (entries with the same primary sort key). Pass these.
        Stop counting when the center_id is passed.
    """
    n = 1
    stopped = True
    for hit in hits:
        if center_id == hit['_id']:
            stopped = True
            break
        n += 1
    # if the center, for some reson, is not among the hits, show all hits
    n = 0 if not stopped else n
    return hits[n:]


# TODO replace with a less hacky function
# originally from
# https://stackoverflow.com/questions/9778550/which-is-the-correct-way-to-encode-escape-characters-in-python-2-without-killing
def control_escape(s):
    """ Escapes control characters so that they can be parsed by a json parser.
    Eg. \u0001 => \\u0001
    Note that u'\u0001'.encode('unicode_escape') will encode the string as
    '\\x01', which do not work for json. Hence the .replace('\\x', '\u00').
    """
    # the set of characters migth need to be extended
    if type(s) is not str and type(s) is not unicode:
        s = str(s)
    control_chars = [unichr(c) for c in range(0x20)]
    return u''.join([c.encode('unicode_escape').replace('\\x', '\u00')
                     if c in control_chars else c for c in s])


def export(lexicon):
    # TODO can user with only read permissions export all the lexicon?
    # (eg saol)
    auth, permitted = validate_user(mode="read")
    if lexicon not in permitted:
        raise errors.KarpAuthenticationError('You are not allowed to search the '
                                         'lexicon %s' % lexicon)

    settings = parser.make_settings(permitted, {"size": -1, "resource": lexicon})
    parser.parse_extra(settings)
    date = settings.get('date', '')
    mode = settings.get('mode', '')
    if date:
        import dateutil.parser as dateP
        from datetime import datetime
        # parse the date as inclusive (including the whole selected day)
        date = dateP.parse(date, dateP.parserinfo(yearfirst=True),
                           default=datetime(1999, 01, 01, 23, 59))

    to_keep = {}
    engine, db_entry = db.get_engine(lexicon, echo=False)
    size = settings['size']
    _logger.debug('exporting %s entries from %s ' % (size, lexicon))
    for entry in db.dbselect(lexicon, engine=engine, db_entry=db_entry,
                             max_hits=size, to_date=date):
        _id = entry['id']
        if _id in to_keep:
            last = to_keep[_id]['date']
            if last < entry['date']:
                to_keep[_id] = entry
        else:
                to_keep[_id] = entry

    ans = [val['doc'] for val in to_keep.values() if val['status'] != 'removed']
    ans = ans[:settings['size']]

    _logger.debug('exporting %s entries' % len(ans))
    if settings.get('format', ''):
        toformat = settings.get('format')
        index, typ = conf_mgr.get_mode_index(mode)
        msg = 'Unkown %s %s for mode %s' % ('format', toformat, mode)
        format_posts = conf_mgr.extra_src(mode, 'exportformat', helpers.notdefined(msg))
        lmf, err = format_posts(ans, lexicon, mode, toformat)
        return Response(lmf, mimetype='text/xml')

    else:
        divsize = 5000
        if len(ans) < divsize:
            _logger.debug('simply sending entries')
            return jsonify({lexicon: ans})
        def gen():
            start, stop = 0, divsize
            yield '{"%s": [' % lexicon
            while start < len(ans):
                _logger.debug('chunk %s - %s' % (start, stop))
                if start > 1:
                    yield ','
                yield ','.join([dumps(obj) for obj in ans[start:stop]])
                #yield dumps(ans[start:stop])
                start = stop
                stop += divsize
            yield ']}'
        _logger.debug('streaming entries')
        return Response(stream_with_context(gen()))


# from korp
def prevent_timeout(generator):
    """Decorator for long-running functions that might otherwise timeout."""
    @functools.wraps(generator)
    def decorated(args=None, *pargs, **kwargs):

        def f(queue):
            for response in generator(args, *pargs, **kwargs):
                queue.put(response)
            # print 'put DONE'
            queue.put("DONE")

        timeout = 10
        q = Queue()

        @copy_current_request_context
        def error_catcher(g, *pargs, **kwargs):
            try:
                g(*pargs, **kwargs)
            except Exception as e:
                q.put(sys.exc_info())

        pool = ThreadPool(1)
        pool.spawn(error_catcher, f, q)

        while True:
            try:
                msg = q.get(block=True, timeout=timeout)
                if msg == "DONE":
                    # print 'got DONE'
                    break
                elif isinstance(msg, tuple):
                    raise Exception(msg)
                else:
                    yield msg
            except Empty:
                yield {}

    return decorated


def main_handler(generator):
    @functools.wraps(generator)  # Copy original function's information, needed by Flask
    def decorated(args=None, *pargs, **kwargs):
        # Function is called externally

        def incremental_json(ff):
            """Incrementally yield result as JSON."""
            yield "{\n"

            try:
                for response in ff:
                    if not response:
                        # Yield whitespace to prevent timeout
                        # print 'prevent timeout'
                        yield " \n"
                    else:
                        # print 'yielding result'
                        yield response  # dumps(response)[1:-1] + ",\n"
            except GeneratorExit:
                raise
            except Exception as e:
                raise
            # print 'main done'
            yield "\n"

        def full_json(ff):
            """Yield full JSON at end, but keep returning newlines to prevent timeout."""
            result = {}

            try:
                for response in ff:
                    if not response:
                        # print 'prevent timeout'
                        # Yield whitespace to prevent timeout
                        yield " \n"
                    else:
                        # print 'update result'
                        result.update(response)
            except GeneratorExit:
                raise
            except:
                raise



            # result = dumps(result)
            # print 'last yield'
            yield result
            # print 'main done'

        # Incremental response
        return Response(stream_with_context(incremental_json(generator(args, *pargs, **kwargs))),
                        mimetype="application/json")
    return decorated


@main_handler
@prevent_timeout
def export2(lexicon, divsize=5000):
    # TODO can user with only read permissions export all the lexicon?
    # (eg saol)
    auth, permitted = validate_user(mode="read")
    if lexicon not in permitted:
        raise errors.KarpAuthenticationError('You are not allowed to search the '
                                         'lexicon %s' % lexicon)

    settings = parser.make_settings(permitted, {"size": -1, "resource": lexicon})
    parser.parse_extra(settings)
    date = settings.get('date', '')
    mode = settings.get('mode', '')
    if date:
        import dateutil.parser as dateP
        from datetime import datetime
        # parse the date as inclusive (including the whole selected day)
        date = dateP.parse(date, dateP.parserinfo(yearfirst=True),
                           default=datetime(1999, 01, 01, 23, 59))

    #def get_data(inp):
    #time.sleep(10)
    to_keep = {}
    engine, db_entry = db.get_engine(lexicon, echo=False)
    size = settings['size']
    # print 'exporting %s entries from %s ' % (size, lexicon)
    for entry in db.dbselect(lexicon, engine=engine, db_entry=db_entry,
                             max_hits=-1, to_date=date):
        _id = entry['id']
        if _id in to_keep:
            last = to_keep[_id]['date']
            if last < entry['date']:
                to_keep[_id] = entry
        else:
                to_keep[_id] = entry

    ans = [val['doc'] for val in to_keep.values() if val['status'] != 'removed']
    # print 'shorten list?'
    if size != float('inf') and size < len(ans):
        # print 'done, %s < %s' % (size, len(ans))
        ans = ans[:settings['size']]
    #inp['out'] = ans
    # print 'I am done!'
    #return

    if settings.get('format', ''):
        #ans = {}
        #get_data(ans)
        #ans = ans['out']
        # print 'exporting %s entries' % len(ans)
        toformat = settings.get('format')
        index, typ = conf_mgr.get_mode_index(mode)
        msg = 'Unkown %s %s for mode %s' % ('format', toformat, mode)
        format_posts = conf_mgr.extra_src(mode, 'exportformat', helpers.notdefined(msg))
        lmf, err = format_posts(ans, lexicon, mode, toformat)
        yield Response(lmf, mimetype='text/xml')

    else:
        #import threading
        #import time
        # print 'divsize %s' % divsize
        divsize = int(divsize)
        #def gen():
        #ans = {}
        #t = threading.Thread(target=get_data, args=[ans])
        #t.start()
        #yield '{"%s": [' % lexicon
        yield '"%s": [' % lexicon
        # while t.is_alive():
        #     yield(' ')
        #     _logger.debug('sleep')
        #     time.sleep(1)
        #     _logger.debug('wake up')

        #print 'thread finished %s' % t.is_alive()
        #ans = ans['out']
        # print 'exporting %s entries' % len(ans)
        start, stop = 0, divsize
        # print 'streaming entries'
        while start < len(ans):
            # print 'chunk %s - %s' % (start, stop)
            if start > 1:
                yield ',\n'
            # print 'preparing a res'
            try:
                res = ','.join([dumps(obj) for obj in ans[start:stop]])
                # print 'yielding a res'
                yield res
                yield '\n'
            except:
                # print 'exception here! % - %s' % start, stop
                raise
            #yield dumps(ans[start:stop])
            start = stop
            stop += divsize
        # print 'done'
        yield ']}\n'
        # return Response(stream_with_context(gen()))
