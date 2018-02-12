# -*- coding: utf-8 -*-
import elasticObjects
from elasticsearch import helpers as EShelpers
from flask import request
import fieldmapping as F
import parsererror as PErr
import src.server.helper.configmanager as configM
import re

import logging
""" Responsible for the translation from the query api to elastic queries """


# TODO removed first argument
def get_mode():
    return request.args.get('mode', configM.standardmode)


def make_settings(permitted, in_settings):
    settings = {"allowed": permitted, 'mode': configM.standardmode}
    settings.update(in_settings)
    return settings


# TODO removed first argument
def parse(settings={}, isfilter=False):
    """ Parses a query on the form simple||..., extended||...
        returns the corresponding elasticsearch query object
        settings is a dictionary where the 'size' (the number of wanted hits)
                 will be set, if included in the query
        isfilter is set to True when a elastic Filter, rather than a query,
                 should be returned
        """
    # isfilter is used for minientries and some queries to statistics
    parsed = request.args
    # only one query is allowed
    query = parsed.get('q', ['']) or parsed.get('query')
    #query = query.decode('utf8')  # use utf8, same as lexiconlist
    p_extra = parse_extra(settings)
    command, query = query.split('||', 1)
    settings['query_command'] = command
    highlight = settings.get('highlight', False)
    mode = settings.get('mode')
    if command == 'simple':
        settings['search_type'] = 'dfs_query_then_fetch'
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


# TODO removed first argument
def get_command():
    query = request.args.get('q', ['']) or request.args.get('query')
    command, query = query.split('||', 1)
    return command


# TODO removed first argument
def parse_extra(settings):
    """ Parses extra information, such as resource and size """
    # TODO specify available options per url/function
    info = []
    available = ['resource', 'size', 'sort', 'q', 'start', 'page', 'buckets',
                 'show', 'show_all', 'status', 'index', 'cardinality',
                 'highlight', 'format', 'export', 'mode', 'center', 'multi',
                 'date']
    for k in request.args.keys():
        if k not in available:
            raise PErr.QueryError("Option not recognized: %s.\
                                   Available options: %s"
                                  % (k, ','.join(available)))

    if 'mode' in request.args:
        # logging.debug('change mode -> %s' % (parsed))
        settings['mode'] = request.args['mode']

    mode = settings.get('mode')
    logging.info('Mode %s' % mode)
    # set resources, based on the query and the user's permissions
    if 'resource' in request.args:
        wanted = request.args['resource'].split(',')
        # TODO this slightly changes the behaviour
        #wanted = sum((request.args['resource'].split(',') for r in request.args['resource']), [])
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

    if 'size' in request.args:
        size = request.args['size']
        settings['size'] = float(size) if size == 'inf' else int(size)
    if 'sort' in request.args:
        #settings['sort'] = F.lookup_multiple(request.args['sort'].split(','), mode)
        # TODO many sort?
        settings['sort'] = sum([F.lookup_multiple(s, mode)
                               for s in request.args['sort'].split(',')], [])
    if 'page' in request.args:
        settings['page'] = min(int(request.args['page'])-1, 0)
    if 'start' in request.args:
        settings['start'] = int(request.args['start'])
    if 'buckets' in request.args:
         settings['buckets'] = [F.lookup(r, mode) for r
                                in request.args['buckets'].split(',')]

    if 'show' in request.args:
        #settings['show'] = F.lookup_multiple(request.args['show'][0].split(','), mode)
        settings['show'] = sum([F.lookup_multiple(s, mode)
                                for s in request.args['show'].split(',')], [])
    # to be used in random
    if 'show_all' in request.args:
        settings['show'] = []

    if 'cardinality' in request.args:
        settings['cardinality'] = True
    if 'highlight' in request.args:
        settings['highlight'] = True

    # status is only used by checksuggestions
    list_flags = ['status', 'index', 'multi']
    for flag in list_flags:
        if flag in request.args:
            settings[flag] = request.args[flag].split(',')

    single_flags = ['format', 'export', 'center', 'q', 'date']
    for flag in single_flags:
        if flag in request.args:
            settings[flag] = request.args[flag]
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
    operation = parse_operation(etype, op, isfilter=isfilter)
    f_query = parse_field(field_info, operation)
    format_query = configM.extra_src(mode, 'format_query', None)
    if format_query is not None:
        # format the operands as specified in the extra src for each mode
        operands = [format_query(field, o) for o in operands]
    logging.debug('construct from %s' % operands)
    q = f_query.construct_query(operands)
    if isfilter or f_query.isfilter:
        # TODO for querycount (statistics) with extended queries
        # if something else breaks, add f_query.ok_in_filter for this instance
        # and uncomment the below if clause
        # if not f_query.ok_in_filter:
        #     q = '"query" : {%s}' % q
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
    highlight = ['*'] if field == 'anything' else fields
    return {"fields": fields, "constraints": constraints,
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


def parse_operation(etype, op, isfilter=False):
    """ Parses an expression type and an operation
        etype is an unparsed string ("and", "not")
        op    is an unparsed string ("equals", "missing", "regexp"...)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        returns an elasticObject
        """
    return elasticObjects.Operator(etype, op, isfilter=isfilter)


def freetext(text, mode, extra=[], isfilter=False, highlight=False):
    """ Constructs a free text query, searching all fields but boostig the
        form and writtenForm fields
        text is the text to search for
        extra is a list of other expressions to include in the query
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a query object to be sent to elastic search

    """
    if 'format_query' in configM.mode_fields(mode):
        # format the query text as specified in settings
        text = configM.formatquery(mode, 'anything', text)

    qs = []
    for field in configM.all_searchfield(mode):
        qs += ['"match": {"%s": {"query": "%s", "operator": "and"}}' % (field, text)]
    # if isfilter:
    #     qs = ['"query" : {%s}' % q for q in qs]

    boost_list = configM.searchfield(mode, 'boosts')
    boost_score = len(boost_list)*100
    for field in boost_list:
        # TODO used to be term, is match ok?
        qs.append('"match": {"%s" : {"query": "%s", "boost": "%d"}}'
                  % (field, text, boost_score))
        boost_score -= 100

    q = '"bool" : {"should" :[%s]}' % ','.join('{'+q+'}' for q in qs)
    if extra:
        q = '"bool" : {"must" :[%s]}' % ','.join('{'+e+'}' for e in [q]+extra)
    if isfilter:
        return '"filter" : {%s}' % q

    if highlight:
        highlight_str = ',"highlight": {"fields": {"*": {"highlight_query": {%s}}}, "require_field_match": false}' % q
    else:
        highlight_str = ''

    logging.debug('WOOW WE HAVE {"query": {%s} %s}' % (q, highlight_str))
    return '{"query": {%s} %s}' % (q, highlight_str)


def search(exps, filters, fields, isfilter=False, highlight=False,
           usefilter=False, constant_score=True):
    """ Combines a list of expressions into one elasticsearch query object
        exps    is a list of strings (unfinished elasticsearch objects)
        filters is a list of filters (unfinished elasticsearch objects)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a string, representing complete elasticsearch object
    """
    logging.debug("start parsing expss %s \n filters %s " % (exps, filters))
    constant_s = ('"constant_score": {"filter": {', '}}') if constant_score else ('', '')
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
        q = construct_exp(exps+filters, querytype="must", constant_score=constant_s[0])
        logging.debug('Constant 0 0: %s \n 1: %s' % (constant_s))
        return '{"query" : {%s "bool": {%s}}%s %s}' % (constant_s[0], q, constant_s[1], highlight_str)

    logging.debug("construct %s " % filters)
    f = construct_exp(filters, querytype="filter")
    logging.debug("got %s\n\n" % f)
    if isfilter:
        return f

    if f and exps:
        q = construct_exp(exps, querytype="must", constant_score=constant_s[0])
        logging.debug('Constant 1 0: %s \n 1: %s' % (constant_s))
        return '{"query": {%s "bool" : {%s,%s}}}%s' % (constant_s[0], f, q, constant_s[1])
    else:
        logging.debug('Constant 2 0: %s \n 1: %s' % (constant_s))
        q = construct_exp(exps, querytype="query", constant_score=constant_s[0])
    return '{%s %s}' % (f+q, highlight_str)


def construct_exp(exps, querytype="filter", constant_score=True):
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

        combinedquery = "filter" if querytype == "must" else querytype
        return '"%s" : {"bool" : {"must" : [%s]}}'\
               % (combinedquery, ','.join('{'+e+'}' for e in exps))
    # otherwise just put the expression in a query
    if constant_score:
        query = '"%s": {"constant_score": {%s}}' % (querytype, exps[0])
    else:
        query = '"%s": {%s}' % (querytype, exps[0])
    return query


# TODO removed first argument
def random(settings):
    resource = parse_extra(settings)
    resource = '"query": {%s}, ' % resource[0] if resource else ''
    elasticq = '''{"query": {"function_score": { %s "random_score": {}}}}
               ''' % (resource)
    logging.debug('Will send %s' % elasticq)
    return elasticq


# TODO removed first argument
def statistics(settings, exclude=[], order={}, prefix='',
               show_missing=True, force_size=-1):
    """ Constructs a ES query for an statistics view (aggregated information)
        Contains the number of hits in each lexicon, grouped by POS
    """
    q = request.args.get('q', '')
    resource = parse_extra(settings)
    # q is the search query and/or the chosen resource
    if q:
        q = parse(isfilter=True, settings=settings)
    else:  # always filter to show only the permitted resources
        q = '"filter" : {%s}' % resource[0]

    buckets = settings.get('buckets')
    logging.debug('buckets %s' % buckets)
    # buckets = buckets - exclude
    if exclude:
        # buckets = buckets - exclude
        # do a set difference operation, but preserve the order
        buckets = [b for b in buckets if b not in exclude]

    if force_size >= 0:
        size = force_size
    else:
        size = settings.get('size')
    to_add = ''
    normal = not settings.get('cardinality')
    more = []  # collect queries about max size for each bucket
    shard_size = 1000  # TODO how big? get from config
    # For saldo:
    # 26 000 => document count errors
    # 27 000 => no errors
    for bucket in reversed(buckets):
        terms = 'terms' if normal else 'cardinality'
        # the sorting order for this bucket, used by querycount
        bucket_order = ''
        if order.get(bucket):
            bucket_order = ',"order" : {"%s": "%s"}' % order.get(bucket)

        # embed previous agg in this one, separate by comma
        to_add = ','+to_add if to_add else to_add

        # add size if the query is normal (i.e. not for cardinality queries)
        add_size = ',"size" : %s, "shard_size": %s' % (size if normal else '', shard_size)

        # construct query for entries with the current field/bucket
        # mode = ', "collect_mode" : "breadth_first"' if normal else ''
        mode = ''
        if len(buckets) > 2 or size > 1000:
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
            add_size = ',"size" : %s, "shard_size": %s' % (min(size or max_size, max_size), shard_size)

        count_errors = ''  # '"show_term_doc_count_error": true, '
        to_add_exist = '"%s%s" : {"%s" : {%s "field" : "%s" %s %s %s} %s}'\
                       % (prefix, bucket, terms, count_errors, bucket,
                          add_size, mode, bucket_order, to_add)

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
    if stop_num <= configM.setupconfig['SCAN_LIMIT']:
        kwargs['body'] = query
        logging.debug('Will ask for %s' % kwargs)
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
        elif tot_hits < configM.setupconfig['SCAN_LIMIT']:
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
