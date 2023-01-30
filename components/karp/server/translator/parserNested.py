# -*- coding: utf-8 -*-
from . import elasticObjects
from urllib.parse import parse_qs
from . import fieldmapping as F
from . import parsererror as PErr
import config.searchconf as conf
import re
""" Responsible for the translation from the query api to elastic queries """


def parse(query, settings={}, highlight=True, isfilter=False):
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
    if command == 'simple':
        return freetext(query, isfilter=isfilter, extra=p_extra,
                        highlight=highlight)
    if command == "extended":
        filters = []  # filters will be put here
        for e in query.split('||'):
            parse_ext(e, p_extra, filters, isfilter=isfilter)

        return search(p_extra, filters, isfilter=isfilter)

    if command == "nested":
        filters = []  # filters will be put here
        for e in query.split('||'):
            parse_ext_nested(e, p_extra, filters, isfilter=isfilter)

        return search(p_extra, filters, isfilter=isfilter)


def parse_extra(parsed, settings):
    """ Parses extra information, such as resource and size """
    # TODO specify available options per url/function
    info = []
    available = ['resource', 'size', 'sort', 'q', 'start', 'page', 'buckets',
                 'show', 'status', 'index', 'cardinality']
    for k in list(parsed.keys()):
        if k not in available:
            raise PErr.QueryError("Option not recognized: %s.\
                                   Available options: %s"
                                  % (k, ','.join(available)))

    # set resources, based on the query and the user's permissions
    if 'resource' in parsed:
        #  TODO what happens if we want to make an update?
        #       does update.py use this?
        wanted = sum((r.split(',') for r in parsed['resource']), [])
    else:
        wanted = []
    ok_lex = []  # lists all allowed lexicons
    for r in settings.get('allowed', []):
        if r in wanted or not wanted:  # TODO inloggning
            ok_lex.append(r)
            info.append('"term" : {"%s" : "%s"}'
                        % (F.lookup("lexiconName"), r))
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
        settings['sort'] = sum([F.lookup_multiple(s)
                                for s in parsed['sort'][0].split(',')], [])
    if 'page' in parsed:
        settings['page'] = min(int(parsed['page'][0])-1, 0)
    if 'start' in parsed:
        settings['start'] = int(parsed['start'][0])
    if 'buckets' in parsed:
        settings['buckets'] = [F.lookup(r) for r
                               in parsed['buckets'][0].split(',')]

    if 'show' in parsed:
        settings['show'] = sum([F.lookup_multiple(s)
                                for s in parsed['show'][0].split(',')], [])
    # this is only used by checksuggestions
    if 'status' in parsed:
        settings['status'] = sum((r.split(',') for r in parsed['status']), [])
    if 'index' in parsed:
        settings['index'] = sum((r.split(',') for r in parsed['index']), [])
    if 'cardinality' in parsed:
        settings['cardinality'] = True
    return info

# TODO nested queries
#def parse_ext_nested(exp, exps, filters, isfilter=False):
#    # q=extended||nested|[wf_inflected|equals|hej||pos|exists]
#    xs = re.search('\[([^]])\]', exp)  # f
#    xs = re.split('(?<!\\\)\|', exp)  # split only on | not preceded by \
#    # xs = exp.split('|')
#    etype, field, op = xs[:3]
#    field_info = get_field(field)
#    operands = [re.sub('\\\\\|', '|', x) for x in xs[3:]]  # replace \| by |
#    operation = parse_operation(etype, op, isfilter=isfilter,
#                                special_op=field_info['op'])
#    f_query = parse_field(field_info, operation)
#    if 'format_query' in dir(conf):
#        # format the operands as specified in settings
#        operands = [conf.format_query(field, o) for o in operands]
#    q = f_query.construct_query(operands)
#    if isfilter or f_query.isfilter:
#        if not f_query.ok_in_filter:
#            q = '"query" : {%s}' % q
#        filters.append(q)
#    else:
#        exps.append(q)
#


def parse_ext(exp, exps, filters, isfilter=False):
    """ Parses one expression from a extended query
        Returns a string, representing an unfinished elasticsearch object
        exp     is the expression to parse
        exps    is a list of already parsed expressions
        filters is a list of already parsed filters """
    xs = re.split('(?<!\\\)\|', exp)  # split only on | not preceded by \
    # xs = exp.split('|')
    etype, field, op = xs[:3]
    field_info = get_field(field)
    operands = [re.sub('\\\\\|', '|', x) for x in xs[3:]]  # replace \| by |
    operation = parse_operation(etype, op, isfilter=isfilter,
                                special_op=field_info['op'])
    f_query = parse_field(field_info, operation)
    if 'format_query' in dir(conf):
        # format the operands as specified in settings
        operands = [conf.format_query(field, o) for o in operands]
    q = f_query.construct_query(operands)
    if isfilter or f_query.isfilter:
        if not f_query.ok_in_filter:
            q = '"query" : {%s}' % q
        filters.append(q)
    else:
        exps.append(q)


def get_field(field):
    """ Parses a field and extract it's special needs
        field  is an unparsed string
        returns a dictionary """
    if field not in F.mappings:  # translate_field:
        raise PErr.QueryError('Not implemented: field "%s"' % field)

    fields, constraints = F.lookup_multiple_spec(field)
    special_op = F.lookup_op(field)
    return {"fields": fields, "constraints": constraints, "op": special_op}


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


def freetext(text, extra=[], isfilter=False, highlight=True):
    """ Constructs a free text query, searching all fields but boostig the
        form and writtenForm fields
        text is the text to search for
        extra is a list of other expressions to include in the query
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a query object to be sent to elastic search
    """
    if 'format_query' in dir(conf):
        # format the query text as specified in settings
        text = conf.format_query('anything', text)
    qs = []
    for field in conf.all_fields:
        qs += ['"match_phrase" :  {"%s" : "%s"}' % (field, text)]
    if isfilter:
        qs = ['"query" : {%s}' % q for q in qs]
    q = '"bool" : {"should" :[%s]}' % ','.join('{'+q+'}' for q in qs)
    if extra:
        q = '"bool" : {"must" :[%s]}' % ','.join('{'+e+'}' for e in [q]+extra)
    if isfilter:
        return '"filter" : {%s}' % q

    if highlight:
        highlight_str = ',"highlight": {"fields": {"*": {}}, "require_field_match": false}'
    else:
        highlight_str = ''

    to_boost = []
    boost_score = len(conf.boosts)*100
    for field in conf.boosts:
        to_boost.append('{"boost_factor": "%d", "filter":{"term":{"%s":"%s"}}}'
                        % (boost_score, field, text))
        boost_score -= 100

    querystring = '''{"query": {"function_score":
                        {"functions": [%s], "query": {%%s} }}%%s}
                  ''' % ','.join(to_boost)
    return querystring % (q, highlight_str)


def search(exps, filters, isfilter=False):
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
    f = construct_exp(filters, querytype="filter")
    if isfilter:
        return f
    if f and exps:
        q = construct_exp(exps, querytype="must")
        return '{"query"  : {"bool" : {%s,%s}}}' % (f, q)
    else:
        q = construct_exp(exps)
    return '{%s}' % (f+q)


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


def statistics(query, settings, order={}, show_missing=True):
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
    size = settings.get('size')
    to_add = ''
    normal = not settings.get('cardinality')
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
        to_add_exist = '"%s" : {"%s" : {"field" : "%s" %s %s} %s}'\
                       % (bucket, terms, bucket, add_size,
                          bucket_order, to_add)

        # construct query for entries missing the current field/bucket
        to_add_missing = '"%s_missing" : {"missing" : {"field" : "%s" %s} %s}'\
                         % (bucket, bucket, bucket_order, to_add)

        # normal queries contain the 'missing' buckets
        if normal and show_missing:
            to_add = '"aggs" : {%s, %s}' % (to_add_exist, to_add_missing)
        # cardinality queries do not
        else:
            to_add = '"aggs" : {%s}' % (to_add_exist)
        # set normal to True, since only the innermost bucket grouping can
        # contain cardinality information
        # (otherwise the innermost won't be shown)
        normal = True

    agg = '{"aggs" : {"q_statistics": {%s, %s}}}' \
          % (q, to_add) if q else '{%s}' % to_add
    return agg


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
