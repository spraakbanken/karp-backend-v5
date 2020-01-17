# -*- coding: utf-8 -*-
""" Responsible for the translation from the query api to elastic queries """

from builtins import range
import logging
import re

from collections import defaultdict
from elasticsearch import helpers as EShelpers
from flask import request

import karp5.server.translator.elasticObjects as elasticObjects

from . import errors
from karp5.config import mgr as conf_mgr


_logger = logging.getLogger("karp5")


def get_mode():
    return request.args.get("mode", conf_mgr.app_config.STANDARDMODE)


def make_settings(permitted, in_settings):
    settings = {"allowed": permitted, "mode": conf_mgr.app_config.STANDARDMODE}
    settings.update(in_settings)
    return settings


def parse(settings=None, isfilter=False):
    """ Parses a query on the form simple||..., extended||...
        returns the corresponding elasticsearch query object
        settings is a dictionary where the 'size' (the number of wanted hits)
                 will be set, if included in the query
        isfilter is set to True when a elastic Filter, rather than a query,
                 should be returned
    """
    if settings is None:
        settings = {}
    # isfilter is used for minientries and some queries to statistics
    # only one query is allowed
    query = request.args.get("q", [""]) or request.args.get("query")
    # query = query.decode('utf8')  # use utf8, same as lexiconlist
    p_extra = parse_extra(settings)
    command, query = query.split("||", 1)
    settings["query_command"] = command
    highlight = settings.get("highlight", False)
    mode = settings.get("mode")
    if command == "simple":
        settings["search_type"] = "dfs_query_then_fetch"
        return freetext(query, mode, isfilter=isfilter, extra=p_extra, highlight=highlight)
    elif command == "extended":
        filters = []  # filters will be put here
        fields = []
        p_ex = [p_extra]
        for e in split_query(query):
            _logger.debug("parsing %s", e)
            if "|||" in e:
                fields.append(parse_nested(e, p_ex, filters, mode, isfilter=isfilter))
            else:
                fields.append(parse_ext(e, p_ex, filters, mode, isfilter=isfilter))
            _logger.debug("fields %s, p_ex %s", fields, p_ex)
        # unless the user wants to sort by _score, use a filter rather
        # than a query. will improve ES speed, since no scoring is done.
        usefilter = "_score" not in settings.get("sort", "")

        return search(
            p_ex, filters, fields, isfilter=isfilter, highlight=highlight, usefilter=usefilter,
        )
    else:
        raise errors.QueryError(
            "Search command not recognized: %s.\
                               Available options: simple, extended"
            % (command)
        )


def get_command():
    query = request.args.get("q", [""]) or request.args.get("query")
    command, query = query.split("||", 1)
    return command


def parse_extra(settings):
    """ Parses extra information, such as resource and size """
    # TODO specify available options per url/function
    lex_wanted = []
    info = {}
    available = [
        "resource",
        "size",
        "sort",
        "q",
        "start",
        "page",
        "buckets",
        "show",
        "show_all",
        "status",
        "index",
        "cardinality",
        "highlight",
        "format",
        "export",
        "mode",
        "center",
        "multi",
        "date",
        "statsize",
    ]
    for k in list(request.args.keys()):
        if k not in available:
            raise errors.QueryError(
                "Option not recognized: %s.\
                                   Available options: %s"
                % (k, ",".join(available))
            )

    if "mode" in request.args:
        # _logger.debug('change mode -> %s' % (parsed))
        settings["mode"] = request.args["mode"]

    mode = settings.get("mode")
    _logger.info("Mode %s", mode)
    # set resources, based on the query and the user's permissions
    if "resource" in request.args:
        wanted = request.args["resource"].split(",")
    else:
        wanted = []
    ok_lex = []  # lists all allowed lexicons
    for r in settings.get("allowed", []):
        if r in wanted or not wanted:
            ok_lex.append(r)
            lex_wanted.append({"term": {conf_mgr.lookup("lexiconName", mode): r}})

    if len(lex_wanted) > 1:
        # if more than one lexicon, the must be put into a 'should' ('or'),
        # not the 'must' query ('and') that will be constructed later
        info = {"bool": {"should": lex_wanted}}
    elif len(lex_wanted) == 1:
        info = lex_wanted[0]

    if not ok_lex:
        # if no lexicon is set, ES will search all lexicons,
        # included protected ones
        raise errors.AuthenticationError(
            "You are not allowed to search any" + " of the requested lexicons"
        )

    # the below line is used by checklexiconhistory and checksuggestions
    settings["resource"] = ok_lex

    if "size" in request.args:
        size = request.args["size"]
        settings["size"] = float(size) if size == "inf" else int(size)
    if "sort" in request.args:
        # settings['sort'] = conf_mgr.lookup_multiple(request.args['sort'].split(','), mode)
        settings["sort"] = sum(
            [conf_mgr.lookup_multiple(s, mode) for s in request.args["sort"].split(",")], [],
        )
    if "page" in request.args:
        settings["page"] = min(int(request.args["page"]) - 1, 0)
    if "start" in request.args:
        settings["start"] = int(request.args["start"])
    if "buckets" in request.args:
        settings["buckets"] = [conf_mgr.lookup(r, mode) for r in request.args["buckets"].split(",")]

    if "show" in request.args:
        # settings['show'] = conf_mgr.lookup_multiple(request.args['show'][0].split(','), mode)
        settings["show"] = sum(
            [conf_mgr.lookup_multiple(s, mode) for s in request.args["show"].split(",")], [],
        )
    # to be used in random
    if "show_all" in request.args:
        settings["show"] = []

    if "statsize" in request.args:
        settings["statsize"] = request.args["statsize"]

    if "cardinality" in request.args:
        settings["cardinality"] = True
    if "highlight" in request.args:
        settings["highlight"] = True

    # status is only used by checksuggestions
    list_flags = ["status", "index", "multi"]
    for flag in list_flags:
        if flag in request.args:
            settings[flag] = request.args[flag].split(",")

    single_flags = ["format", "export", "center", "q", "date"]
    for flag in single_flags:
        if flag in request.args:
            settings[flag] = request.args[flag]
    return info


def parse_ext(exp, exps, filters, mode, isfilter=False):
    """ Parse one expression from a extended query.

        Returns a dictionary of information about the search field used
        Appends the search equry to exps

        exp     is the expression to parse
        exps    is a list of already parsed expressions
        filters is a list of already parsed filters
        mode    is the current mode
    """
    xs = re.split(r"(?<!\\)\|", exp)  # split only on | not preceded by \
    # xs = exp.split('|')
    etype, field, op = xs[:3]
    field_info = get_field(field, mode)
    operands = [re.sub(r"\\\\\|", "|", x) for x in xs[3:]]  # replace \| by |
    _logger.debug("operands: {0}".format(operands))
    operation = parse_operation(etype, op, isfilter=isfilter)
    f_query = parse_field(field_info, operation)
    format_query = conf_mgr.extra_src(mode, "format_query", None)
    if format_query is not None:
        # format the operands as specified in the extra src for each mode
        operands = [format_query(field, o) for o in operands]
    _logger.debug("construct from %s", operands)
    _logger.debug("f_query %s", f_query)
    q = f_query.construct_query(operands)
    if isfilter or f_query.isfilter:
        _logger.debug("filter %s, %s", q, filters)
        filters.append(q)
    else:
        _logger.debug("extend %s, %s", q, exps)
        exps.append(q)
        field_info["highlight_query"] = q
    return field_info


def parse_nested(exp, exps, filters, mode, isfilter=False):
    """
    Parses a nested expression
        (eg 'and||wf|equals|katt|||msd|equals|sg+def+nom')
        and construct a ES query.
        Appends the resulting search equry to exps.

        Returns a dictionary of information about the search field used

        exp     is the expression to parse
        exps    is a list of already parsed expressions
        filters is a list of already parsed filters
        mode    is the current mode
    """
    qs = exp.split("|||")
    allpaths = []  # will contain all search all queried paths
    todo = {}  # will contain all expressions to construct for every path
    for n, q in enumerate(qs):
        newexps, newfilters = [], []
        # hax, construct complete expression for parsing.
        if n:
            q = "and|" + q
        info = parse_ext(q, newexps, newfilters, mode, isfilter)
        allpaths.extend(info.get("fields"))
        if len(info.get("fields")) > 1:
            # a field may correspond to several paths, not ok for nested queries
            raise errors.QueryError(
                "Cannot construct nested query from multiple fields.\
                                   You attempt to search all of %s."
                % (",".join(info.get("fields")))
            )
        todo[info.get("fields")[0]] = newexps

    # A complicated way to construct the nested query.
    # First, find all fields that are sieblings (grouped together by common_path())
    # and construct queries. Then see if there are higher levels
    # of this nesting. If so, include the deeper nestings inside higher.
    # Start with the longest path, ie the deepest nesting.
    # The fields "a.e", "a.b.c", "a.b.d" should result in the query
    # {"nested": {"path": "a",
    #   "query": {"bool": {"must": {"nested": {"path": "a.b", ...}}}}}}
    tmp = defaultdict(list)
    nesteds = {}
    for ixx, (commonpath, paths) in enumerate(common_path(allpaths).items()):
        q = [todo[path] for path in paths]
        # have we alreay constructed a query for an inner nesting?
        for inner in tmp[commonpath]:
            # if so, merge with this and remove the previous
            if nesteds.get(inner, ""):
                q.append(nesteds[inner])
                nesteds[inner] = ""

        exp = {"nested": {"path": commonpath, "query": {"bool": {"must": q}}}}
        nesteds[ixx] = exp

        for ix in range(len(commonpath.split("."))):
            part = commonpath.split(".", ix)[0]
            tmp[part].append(ixx)

    # Finally, append all nested queries.
    # Exclude queries already used inside others
    for ix in set(sum(list(tmp.values()), [])):
        if nesteds[ix]:
            _logger.debug("add nested %s: %s", ix, nesteds[ix])
            exps.append(nesteds[ix])

    # TODO what to do with filters?? most likely always empty
    # (filters should be removed from the code)
    return info


def common_path(fields):
    """ Group a list of fields into a dictionary of common parents
        ["a.b.d", "a.b.c", "a.e", "a.b.d.f"]
        =>
        {"a": ["a.e"],
         "a.b": ["a.b.d", "a.b.c"],
         "a.b.d": ["a.b.d.f"]
         }"
    """
    import itertools as i

    grouped = i.groupby(
        sorted(fields, key=lambda x: (len(x.split(".")), "".join(x))),
        key=lambda x: x.split(".")[:-1],
    )
    groups = {}
    for key, group in grouped:
        groups[".".join(key)] = list(group)
    return groups


def get_field(field, mode):
    """ Parses a field and extract it's special needs
        field  is an unparsed string
        returns a dictionary """

    fields, constraints = conf_mgr.lookup_multiple_spec(field, mode)
    highlight = ["*"] if field == "anything" else fields
    return {"fields": fields, "constraints": constraints, "highlight": highlight}


def parse_field(field_info, op):
    """ Combines a field with the operation object
        field_info  is a dictionary containing at least the key 'fields'
        op     is an elasticObject
        returns an elasticObject """

    fields = field_info["fields"]
    constraints = field_info["constraints"]
    _logger.debug("fields %s", fields)
    if len(fields) > 1 or constraints:
        # If there's more than one field, use the multiple_field_string
        op.multiple_fields_string(fields=fields, constraints=constraints)
    else:
        # otherwise use the standard string
        op.set_field(field=fields[0])
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


def freetext(text, mode, extra=None, isfilter=False, highlight=False):
    """ Constructs a free text query, searching all fields but boostig the
        form and writtenForm fields
        text is the text to search for
        extra is a list of other expressions to include in the query
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a query object to be sent to elastic search

    """
    if extra is None:
        extra = {}
    if "format_query" in conf_mgr.mode_fields(mode):
        # format the query text as specified in settings
        text = conf_mgr.formatquery(mode, "anything", text)

    qs = []
    for field in conf_mgr.all_searchfield(mode):
        qs.append({"match": {field: {"query": text, "operator": "and"}}})

    boost_list = conf_mgr.searchfield(mode, "boosts")
    boost_score = len(boost_list) * 100
    for field in boost_list:
        qs.append({"match": {field: {"query": text, "boost": boost_score}}})
        boost_score -= 100

    q = {"bool": {"should": [qs]}}
    if extra:
        q = {"bool": {"must": [q, extra]}}
    if isfilter:
        return {"filter": q}

    res = {"query": q}
    if highlight:
        res["highlight"] = {
            "fields": {"*": {"highlight_query": q}},
            "require_field_match": False,
        }
    return res


def search(
    exps, filters, fields, isfilter=False, highlight=False, usefilter=False, constant_score=True,
):
    """ Combines a list of expressions into one elasticsearch query object
        exps    is a list of strings (unfinished elasticsearch objects)
        filters is a list of filters (unfinished elasticsearch objects)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
        Returns a string, representing complete elasticsearch object
    """
    _logger.debug("start parsing expss %s \n filters %s ", exps, filters)
    if isfilter:
        filters += exps  # add to filter list
        exps = []  # nothing left to put in query

    # extended queries: always use filter, scoring is never used
    res = {}
    if usefilter and not isfilter:
        _logger.debug("case 1")
        q_obj = construct_exp(exps + filters, querytype="must", constant_score=constant_score)
        q_obj = {"bool": q_obj}

    else:
        _logger.debug("construct %s ", filters)
        f_obj = construct_exp(filters, querytype="filter")
        _logger.debug("got %s\n\n", f_obj)
        if isfilter:
            _logger.debug("case 2")
            q_obj = f_obj

        elif f_obj and exps:
            _logger.debug("case 3")
            qs = construct_exp(exps, querytype="must", constant_score=constant_score)
            qs.update(f_obj)
            q_obj = {"bool": qs}
        else:
            _logger.debug("case 4")
            q_obj = construct_exp(exps, querytype="query", constant_score=constant_score)
            _logger.debug("got %s", q_obj)

    if constant_score and usefilter and not isfilter:
        res["constant_score"] = {"filter": q_obj}
        res = {"query": res}
    else:
        res = q_obj
    if highlight:
        high_fields = {}
        for field_q in fields:
            _logger.debug("field_q %s", field_q)
            for field in field_q["fields"]:
                high_fields[field] = {
                    "number_of_fragments": 0,
                    "highlight_query": field_q["highlight_query"],
                    "require_field_match": False,
                }

        res["highlight"] = {"fields": high_fields, "require_field_match": False}
        _logger.debug("highlight %s", res["highlight"])

    return res


def construct_exp(exps, querytype="filter", constant_score=True):
    """ Creates the final search object
        Returns a string representing the query object
        exps is a list of strings (unfinished elasticsearch objects)
        isfilter should be set to True when a filter, rather than a query,
                 is wanted
    """
    _logger.debug("exps %s", exps)
    if not exps:
        return ""
    if isinstance(exps, list):
        # If there are more than one expression,
        # combine them with 'must' (=boolean 'and')
        if querytype == "must":
            return {"must": exps}

        combinedquery = "filter" if querytype == "must" else querytype
        return {combinedquery: {"bool": {"must": exps}}}
    # otherwise just put the expression in a query
    if constant_score:
        query = {querytype: {"constant_score": exps}}
    else:
        query = {querytype: exps}
    return query


def random(settings):
    resource = parse_extra(settings)
    elasticq = {"query": {"function_score": {"random_score": {}}}}
    if resource:
        elasticq["query"]["function_score"]["query"] = resource
    _logger.debug("Will send %s", elasticq)
    return elasticq


def statistics(settings, exclude=[], order={}, prefix="", show_missing=True, force_size=-1):
    """ Construct a ES query for an statistics view (aggregated information).

        Contains the number of hits in each lexicon, grouped by POS.
    """
    q = request.args.get("q", "")
    resource = parse_extra(settings)
    # q is the search query and/or the chosen resource
    if q:
        q = parse(isfilter=True, settings=settings)
    else:  # always filter to show only the permitted resources
        q = {"filter": resource}

    buckets = settings.get("buckets")
    _logger.debug("buckets %s", buckets)
    # buckets = buckets - exclude
    if exclude:
        # buckets = buckets - exclude
        # do a set difference operation, but preserve the order
        buckets = [b for b in buckets if b not in exclude]

    if force_size >= 0:
        size = force_size
    else:
        size = settings.get("size")
    to_add = []
    normal = not settings.get("cardinality")
    more = []  # collect queries about max size for each bucket
    shard_size = 27000  # TODO how big? get from config
    # For saldo:
    # 26 000 => document count errors
    # 27 000 => no errors
    bucket_settings = {}
    for bucket in reversed(buckets):
        terms = "terms" if normal else "cardinality"
        # the sorting order for this bucket, used by querycount
        if bucket in order:
            if "order" not in bucket_settings:
                bucket_settings["order"] = {}
            bucket_settings["order"]["bucket"] = order[bucket]

        # add size if the query is normal (i.e. not for cardinality queries)
        bucket_settings = {}
        if normal:
            bucket_settings["size"] = size
            bucket_settings["shard_size"] = shard_size
        # else:
        #    add_size = ''

        # construct query for entries with the current field/bucket
        # mode = ', "collect_mode" : "breadth_first"' if normal else ''
        if normal and (len(buckets) > 2 or size > 1000):
            # TODO to avoid es breaking, do not allow arbitrary deep bucketing
            # If the size is very small, also use breadth_first since it will
            # be faster
            # This should be handled more elegant, but we add strict limits
            # for now, to make sure that the cluster does not run out of memory

            # breadth_first might make the query slower, but helps avoiding
            # memory problems
            # TODO breadth_first should only be used when size is really small
            bucket_settings["collect_mode"] = "breadth_first"
            # if there are more than 3 buckets, also restrict the size
            max_size = 10000
            bucket_settings["size"] = min(size or max_size, max_size)
            bucket_settings["shard_size"] = shard_size

        # count_errors = ''  # '"show_term_doc_count_error": true, '
        to_add_field = "%s%s" % (prefix, bucket)
        # to_add_exist = '"%s%s" : {"%s" : {%s "field" : "%s" %s %s %s} %s}'\
        to_add_exist = {terms: {"field": bucket}}

        # construct query for entries missing the current field/bucket
        missing_field = "%s%s_missing" % (prefix, bucket)
        to_add_missing = {"missing": {"field": bucket}}

        if to_add:
            to_add_exist["aggs"] = to_add
            to_add_missing["aggs"] = to_add

        for key, val in list(bucket_settings.items()):
            to_add_exist[terms][key] = val
            if key == "order":
                to_add_missing["missing"][key] = val

        # normal queries contain the 'missing' buckets
        if normal and show_missing:
            to_add = {to_add_field: to_add_exist, missing_field: to_add_missing}
        # cardinality queries do not
        else:
            to_add = {to_add_field: to_add_exist}
        # construct a query to see the cardinality of this field
        more.append(({"aggs": {"more": {"cardinality": {"field": bucket}}}}, bucket))
        # set normal to True, since only the innermost bucket grouping can
        # contain cardinality information
        # (otherwise the innermost won't be shown)
        normal = True

    agg = {"aggs": to_add}

    if q:
        agg = {"q_statistics": {"aggs": to_add}}
    else:
        agg = to_add

    for key, val in list(q.items()):
        agg["q_statistics"][key] = val

    return {"aggs": agg}, more


def adapt_query(size, _from, es, query, kwargs):
    """ Turns deep pagination queries into scan/scroll requests
        This is needed since ES2 does not allow more than 10 000 hits (even if
        only the last 25 is being asked for).
        Naturally, these queries might be very time consuming
    """
    _logger.debug(
        "|adapt_query| size=%d, _from=%d, query=%s, kwargs=%s", size, _from, query, kwargs
    )
    stop_num = size + max(1, _from)

    # If _from is a float ignore it. Typically this happens because size is
    # inf and neither _from nor page were not set, which will set _from to
    # page*size = 0*inf = nan
    if isinstance(_from, float):
        del kwargs["from_"]

    # If the wanted number of hits is below the scan limit, do a normal search
    if stop_num <= min(conf_mgr.app_config.SCAN_LIMIT, 10000):
        kwargs["body"] = query
        _logger.debug("|adapt_query| Will ask for %s", kwargs)
        return es.search(**kwargs)

    # Else the number of hits is too large, do a scan search
    else:
        # If size is set to infiniy, return all hits
        if size == float("inf"):
            del kwargs["size"]

        # Construct an empty query to ES, to get an return object
        # and the total number of hits
        q_kwargs = {"size": 0, "from_": 0}
        for k, v in list(kwargs.items()):
            if k == "query":
                q_kwargs["body"] = v
            elif k not in ["size", "from_"]:
                q_kwargs[k] = v

        esans = es.search(**q_kwargs)
        tot_hits = esans.get("hits", {}).get("total", 0)

        # If the total number of hits are less then the start number,
        # there is nothing more to find, return the empty answer
        if tot_hits < _from:
            return esans
        # If the total number of hits are less than the scan limit,
        # do a normal search
        elif tot_hits < conf_mgr.app_config.SCAN_LIMIT:
            kwargs["body"] = query
            kwargs["size"] = tot_hits
            return es.search(**kwargs)

        # Else, proceed with the scan
        kwargs["query"] = query
        index = 0

        # Do a full scan of the query result and keep the sorting order
        if "from_" in kwargs:
            del kwargs["from_"]
        scan = EShelpers.scan(es, scroll="5m", preserve_order=True, **kwargs)
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

        _logger.debug("Finished scrolling")
        esans["hits"]["hits"] = hits
        return esans


def split_query(query):
    expressions = []
    start = 0
    for match in re.finditer(r"(?<!\|)\|\|(?!\|)", query):
        newstart, stop = match.span()
        e = query[start:newstart]
        start = stop
        expressions.append(e)
    expressions.append(query[start:])
    return expressions


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
