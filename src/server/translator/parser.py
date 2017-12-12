# -*- coding: utf-8 -*-
from config import setup as setupconf
import elasticObjects
from elasticsearch import helpers as EShelpers
import fieldmapping as F
import parsererror as PErr
import src.server.helper.configmanager as searchconf
import re
from urlparse import parse_qs

import logging
""" Responsible for the translation from the query api to elastic queries """


def get_mode(query):
    return parse_qs(query).get('mode', ['karp'])[0]


def make_settings(permitted, in_settings):
    settings = {"allowed": permitted, 'mode': 'karp'}
    settings.update(in_settings)
    return settings


def parse(query, settings={}, isfilter=False):
    """ Parses a query on the form simple||..., extended||...
        returns the corresponding elasticsearch query object
        settings is a dictionary where the 'size' (the number of wanted hits)
                 will be set, if included in the query
        isfilter is set to True when a elastic Filter, rather than a query,
                 should be returned
        """
    # isfilter is used for minientries and some queries to statistics
    parsed = parse_qs(query)
    # only one query is allowed
    query = parsed.get('q', [''])[0] or parsed.get('query')
    query = query.decode('utf8')  # use utf8, same as lexiconlist
    p_extra = parse_extra(parsed, settings)
    command, query = query.split('||', 1)
    settings['query_command'] = command
    highlight = settings.get('highlight', False)
    mode = settings.get('mode')
    if command == 'simple':
        return freetext(query, mode, isfilter=isfilter, extra=p_extra,
                        highlight=highlight)
    if command == "extended":
        filters = []  # filters will be put here
        fields = []
        for e in query.split('||'):
            fields.append(parse_ext(e, p_extra, filters, mode,
                                    isfilter=isfilter))
        # unless the user wants to sort by _score, use a filter rather
        # than a query. will improve ES speed, since no scoring is done.
        usefilter = '_score' not in settings.get('sort', '')

        return search(p_extra, filters, fields, isfilter=isfilter,
                      highlight=highlight, usefilter=usefilter)


def get_command(query):
    parsed = parse_qs(query)
    query = parsed.get('q', [''])[0] or parsed.get('query')
    command, query = query.split('||', 1)
    return command


def parse_extra(parsed, settings):
    """ Parses extra information, such as resource and size """
    # TODO specify available options per url/function
    info = []
    available = ['resource', 'size', 'sort', 'q', 'start', 'page', 'buckets',
                 'show', 'show_all', 'status', 'index', 'cardinality',
                 'highlight', 'format', 'export', 'mode', 'center', 'multi',
                 'date']
    for k in parsed.keys():
        if k not in available:
            raise PErr.QueryError("Option not recognized: %s.\
                                   Available options: %s"
                                  % (k, ','.join(available)))

    if 'mode' in parsed:
        # logging.debug('change mode -> %s' % (parsed))
        settings['mode'] = parsed['mode'][0]

    mode = settings.get('mode')
    logging.info('Mode %s' % mode)
    # set resources, based on the query and the user's permissions
    if 'resource' in parsed:
        wanted = sum((r.split(',') for r in parsed['resource']), [])
    else:
        wanted = []
    ok_lex = []  # lists all allowed lexicons
    for r in settings.get('allowed', []):
        if r in wanted or not wanted:
            ok_lex.append(r)
            info.append('"term" : {"%s" : "%s"}'
                        % (F.lookup("lexiconName", mode), r))

    if len(info) > 1:
        # if more than one lexicon, the must be put into a 'should' ('or'),
        # not the 'must' query ('and') that will be constructed later
        info = ['"bool" : {"should" : [%s]}'
                % ','.join('{'+i+'}' for i in info)]

    if not ok_lex:
        # if no lexicon is set, ES will search all lexicons,
        # included protected ones
        raise PErr.AuthenticationError("You are not allowed to search any" +
                                       " of the requested lexicons")

    # the below line is used by checklexiconhistory and checksuggestions
    settings['resource'] = ok_lex

    if 'size' in parsed:
        size = parsed['size'][0]
        settings['size'] = float(size) if size == 'inf' else int(size)
    if 'sort' in parsed:
        # TODO many sort?
        settings['sort'] = sum([F.lookup_multiple(s, mode)
                                for s in parsed['sort'][0].split(',')], [])
    if 'page' in parsed:
        settings['page'] = min(int(parsed['page'][0])-1, 0)
    if 'start' in parsed:
        settings['start'] = int(parsed['start'][0])
    if 'buckets' in parsed:
        settings['buckets'] = [F.lookup(r, mode) for r
                               in parsed['buckets'][0].split(',')]

    if 'show' in parsed:
        settings['show'] = sum([F.lookup_multiple(s, mode)
                                for s in parsed['show'][0].split(',')], [])
    # to be used in random
    if 'show_all' in parsed:
        settings['show'] = []

    if 'cardinality' in parsed:
        settings['cardinality'] = True
    if 'highlight' in parsed:
        settings['highlight'] = True

    # status is only used by checksuggestions
    list_flags = ['status', 'index', 'multi']
    for flag in list_flags:
        if flag in parsed:
            settings[flag] = sum((r.split(',') for r in parsed[flag]), [])

    single_flags = ['format', 'export', 'center', 'q', 'date']
    for flag in single_flags:
        if flag in parsed:
            settings[flag] = parsed[flag][0]
    return info


def parse_ext(exp, exps, filters, mode, isfilter=False):
    """ Parses one expression from a extended query
        Returns a string, representing an unfinished elasticsearch object
        exp     is the expression to parse
        exps    is a list of already parsed expressions
        filters is a list of already parsed filters """
    xs = re.split('(?<!\\\)\|', exp)  # split only on | not preceded by \
    # xs = exp.split('|')
    etype, field, op = xs[:3]
    field_info = get_field(field, mode)
    operands = [re.sub('\\\\\|', '|', x) for x in xs[3:]]  # replace \| by |
    operation = parse_operation(etype, op, isfilter=isfilter,
                                special_op=field_info['op'])
    f_query = parse_field(field_info, operation)
    if 'format_query' in searchconf.mode_fields(mode):
        # format the operands as specified in settings
        operands = [searchconf.formatquery(mode, field, o) for o in operands]
    q = f_query.construct_query(operands)
    if isfilter or f_query.isfilter:
        if not f_query.ok_in_filter:
            q = '"query" : {%s}' % q
        filters.append(q)
    else:
        exps.append(q)
        field_info['highlight_query'] = q
    return field_info


def get_field(field, mode):
    """ Parses a field and extract it's special needs
        field  is an unparsed string
        returns a dictionary """

    fields, constraints = F.lookup_multiple_spec(field, mode)
    special_op = searchconf.lookup_op(field, mode)
    highlight = ['*'] if field == 'anything' else fields
    return {"fields": fields, "constraints": constraints, "op": special_op,
            "highlight": highlight}


def parse_field(field_info, op):
    """ Combines a field with the operation object
        field_info  is a dictionary containing at least the key 'fields'
        op     is an elasticObject
        returns an elasticObject """

    fields = field_info['fields']
    constraints = field_info['constraints']
    if len(fields) > 1 or constraints:
        # If there's more than one field, use the multiple_field_string
        op.multiple_fields_string(fields=fields, constraints=constraints)
    else:
        # otherwise use the standard string
        op.string(field=fields[0])
    return op


def parse_operation(etype, op, isfilter=False, special_op={}):
    """ Parses an expression type and an operation
        etype is an unparsed string ("and", "not")
        op    is an unparsed string ("equals", "missing", "regexp"...)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        returns an elasticObject
        """
    return elasticObjects.Operator(etype, op, isfilter=isfilter,
                                   special_op=special_op)


def freetext(text, mode, extra=[], isfilter=False, highlight=False):
    """ Constructs a free text query, searching all fields but boostig the
        form and writtenForm fields
        text is the text to search for
        extra is a list of other expressions to include in the query
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a query object to be sent to elastic search

    """
    if 'format_query' in searchconf.mode_fields(mode):
        # format the query text as specified in settings
        text = searchconf.formatquery(mode, 'anything', text)

    qs = []
    for field in searchconf.searchfield(mode, 'all_fields'):
        qs += ['"match": {"%s": {"query": "%s", "operator": "and"}}' % (field, text)]
    if isfilter:
        qs = ['"query" : {%s}' % q for q in qs]

    q = '"bool" : {"should" :[%s]}' % ','.join('{'+q+'}' for q in qs)
    if extra:
        q = '"bool" : {"must" :[%s]}' % ','.join('{'+e+'}' for e in [q]+extra)
    if isfilter:
        return '"filter" : {%s}' % q

    if highlight:
        highlight_str = ',"highlight": {"fields": {"*": {"highlight_query": {%s}}}, "require_field_match": false}' % q
    else:
        highlight_str = ''

    to_boost = []
    boost_list = searchconf.searchfield(mode, 'boosts')
    boost_score = len(boost_list)*100
    for field in boost_list:
        to_boost.append('{"boost_factor": "%d", "filter":{"term":{"%s":"%s"}}}'
                        % (boost_score, field, text))
        boost_score -= 100

    querystring = '''{"query": {"function_score":
                        {"functions": [%s], "query": {%%s} }}%%s}
                  ''' % ','.join(to_boost)
    return querystring % (q, highlight_str)


def search(exps, filters, fields, isfilter=False, highlight=False, usefilter=False):
    """ Combines a list of expressions into one elasticsearch query object
        exps    is a list of strings (unfinished elasticsearch objects)
        filters is a list of filters (unfinished elasticsearch objects)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a string, representing complete elasticsearch object
    """
    if isfilter:  # add to filter list
        filters += exps
        exps = []  # nothing left to put in query

    if highlight:
        field_query = []
        for field_q in fields:
            high_str = '"highlight_query": {%s}' % field_q["highlight_query"]
            for f in field_q["highlight"]:
                field_query.append((f, high_str))
        # TODO require_field_match should be true only
        # when the field '*' is queried
        field_str = '"%s": {"number_of_fragments": 0, %s, "require_field_match": false}'
        fields = ', '.join([field_str % f for f in field_query])
        highlight_str = ',"highlight": {"fields": {%s}, "require_field_match": false}' % fields
    else:
        highlight_str = ''

    # extended queries: always use filter, scoring is never used
    if usefilter and not isfilter:
        q = construct_exp(exps+filters, querytype="must")
        return '{"query"  : {"bool" : {"filter": {"bool": {%s}}}} %s}' % (q, highlight_str)

    f = construct_exp(filters, querytype="filter")
    if isfilter:
        return f

    if f and exps:
        q = construct_exp(exps, querytype="must")
        return '{"query"  : {"bool" : {%s,%s}}}' % (f, q)
    else:
        q = construct_exp(exps)
    return '{%s %s}' % (f+q, highlight_str)


def construct_exp(exps, querytype="query"):
    """ Creates the final search object
        Returns a string representing the query object
        exps is a list of strings (unfinished elasticsearch objects)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
    """
    if not exps:
        return ''
    if len(exps) > 1:
        # If there are more than one expression,
        # combine them with 'must' (=boolean 'and')
        if querytype == "must":
            return '"must" : [%s]' % ','.join('{'+e+'}' for e in exps)

        combinedquery = "query" if querytype == "must" else querytype
        return '"%s" : {"bool" : {"must" : [%s]}}'\
               % (combinedquery, ','.join('{'+e+'}' for e in exps))
    # otherwise just put the expression in a query
    return '"%s" : {%s}' % (querytype, exps[0])


def random(query, settings):
    import random
    parsed = parse_qs(query)
    resource = parse_extra(parsed, settings)
    resource = '"filter": {%s}, ' % resource[0] if resource else ''
    seed = random.random()
    elasticq = '''{"query": {"function_score": { %s "functions":
                   [{"random_score": {"seed":  "%s" }}], "score_mode": "sum"}}}
               ''' % (resource, seed)
    return elasticq


def statistics(query, settings, exclude=[], order={}, prefix='',
               show_missing=True, force_size=-1):
    """ Constructs a ES query for an statistics view (aggregated information)
        Contains the number of hits in each lexicon, grouped by POS
    """
    parsed = parse_qs(query)
    q = parsed.get('q', '')
    resource = parse_extra(parsed, settings)
    # q is the search query and/or the chosen resource
    if q:
        q = parse(query, isfilter=True, settings=settings)
    else:  # always filter to show only the permitted resources
        q = '"filter" : {%s}' % resource[0]

    buckets = settings.get('buckets')
    # buckets = buckets - exclude
    if exclude:
        buckets = list(set(buckets).difference(exclude))

    if force_size >= 0:
        size = force_size
    else:
        size = settings.get('size')
    to_add = ''
    normal = not settings.get('cardinality')
    more = []  # collect queries about max size for each bucket
    for bucket in reversed(buckets):
        terms = 'terms' if normal else 'cardinality'
        # the sorting order for this bucket, used by querycount
        bucket_order = ''
        if order.get(bucket):
            bucket_order = ',"order" : {"%s": "%s"}' % order.get(bucket)

        # embed previous agg in this one, separate by comma
        to_add = ','+to_add if to_add else to_add

        # add size if the query is normal (i.e. not for cardinality queries)
        add_size = ',"size" : %s' % size if normal else ''

        # construct query for entries with the current field/bucket
        # mode = ', "collect_mode" : "breadth_first"' if normal else ''
        mode = ''
        if len(buckets) > 3 or size > 1000:
            # TODO to avoid es breaking, do not allow arbitrary deep bucketing
            # If the size is very small, also use breadth_first since it will
            # be faster
            # This should be handled more elegant, but we add strict limits
            # for now, to make sure that the cluster does not run out of memory

            # breadth_first might make the query slower, but helps avoiding
            # memory problems
            # TODO breadth_first should only be used when size is really small
            mode = ', "collect_mode" : "breadth_first"'
            # if there are more than 3 buckets, also restrict the size
            max_size = 10000
            add_size = ',"size" : %s' % min(size or max_size, max_size)

        to_add_exist = '"%s%s" : {"%s" : {"field" : "%s" %s %s %s} %s}'\
                       % (prefix, bucket, terms, bucket, add_size,
                          mode, bucket_order, to_add)

        # construct query for entries missing the current field/bucket
        to_add_missing = '"%s%s_missing" : {"missing" : {"field" : "%s" %s} %s}'\
                         % (prefix, bucket, bucket, bucket_order, to_add)

        # normal queries contain the 'missing' buckets
        if normal and show_missing:
            to_add = '"aggs" : {%s, %s}' % (to_add_exist, to_add_missing)
        # cardinality queries do not
        else:
            to_add = '"aggs" : {%s}' % (to_add_exist)
        # construct a query to see the cardinality of this field
        more.append(('{"aggs": {"more" : {"cardinality" : {"field" : "%s"}}}}'
                    % bucket, bucket))
        # set normal to True, since only the innermost bucket grouping can
        # contain cardinality information
        # (otherwise the innermost won't be shown)
        normal = True

    agg = '{"aggs" : {"q_statistics": {%s, %s}}}' \
          % (q, to_add) if q else '{%s}' % to_add
    return agg, more


def adapt_query(size, _from, es, query, kwargs):
    """ Turns deep pagination queries into scan/scroll requests
        This is needed since ES2 does not allow more than 10 000 hits (even if
        only the last 25 is being asked for).
        Naturally, these queries might be very time consuming
    """
    stop_num = size + max(1, _from)

    # If _from is a float ignore it. Typically this happens because size is
    # inf and neither _from nor page were not set, which will set _from to
    # page*size = 0*inf = nan
    if type(_from) == float:
        del kwargs['from_']

    # If the wanted number of hits is below the scan limit, do a normal search
    if stop_num <= setupconf.scan_limit:
        kwargs['body'] = query
        return es.search(**kwargs)

    # Else the number of hits is too large, do a scan search
    else:
        # If size is set to infiniy, return all hits
        if size == float('inf'):
            del kwargs['size']

        # Construct an empty query to ES, to get an return object
        # and the total number of hits
        q_kwargs = {'size': 0, 'from_': 0}
        for k, v in kwargs.items():
            if k == 'query':
                q_kwargs['body'] = v
            elif k not in ['size', 'from_']:
                q_kwargs[k] = v

        esans = es.search(**q_kwargs)
        tot_hits = esans.get('hits', {}).get('total', 0)

        # If the total number of hits are less then the start number,
        # there is nothing more to find, return the empty answer
        if tot_hits < _from:
            return esans
        # If the total number of hits are less than the scan limit,
        # do a normal search
        elif tot_hits < setupconf.scan_limit:
            kwargs['body'] = query
            kwargs['size'] = tot_hits
            return es.search(**kwargs)

        # Else, proceed with the scan
        kwargs['query'] = query
        index = 0

        # Do a full scan of the query result and keep the sorting order
        scan = EShelpers.scan(es, scroll=u'5m', preserve_order=True, **kwargs)
        hits = []
        for hit in scan:
            if index < _from:
                # Skip all hits until the 'from' limit is reached
                pass
            elif index > stop_num:
                # Stop when we reached the max size
                break
            else:
                # Keep the results from the required page
                hits.append(hit)
            index += 1

        logging.debug("Finished scrolling")
        esans['hits']['hits'] = hits
        return esans
# Query -> SimpleQuery
# Query -> ExtendedQuery
# SimpleQuery -> "simple"||<sträng>
# ExtendedQuery -> "extended"(||Expression)+
# Expression -> ExpressionType|Field|BinaryOperator(|Operand)+
# Expression -> ExpressionType|Field|UnaryOperator
# ExpressionType -> "and"
# ExpressionType -> "not"
# Field -> pos, writtenForm eller vad det nu kan vara
# BinaryOperator -> där får vi komma överens om vad som är rimligt att stödja
# UnaryOperator -> just nu bara 'missing', att det inte finns något sådant
#                  fält, men 'exists' hade väl varit bra också
# Operand -> vad som helst i princip
# case sensitive, fuzzy och sånt.


# utanför queryn i egna rest-parametrar, t.ex:
# • mini-entries=true
#   där man då med info=<fältnamn>(|<fältnamn>)* kan ange vilka delar av
#   ingångarna man vill ha levererade.
# • resource=<resursnamn>(|resursnamn)* för vilka lexikon man vill söka i
# • limit=<antal träffar>, respektive limit-start-item:<börja träffarna på>
