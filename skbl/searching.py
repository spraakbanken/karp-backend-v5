import src.server.helper.configmanager as configM


lexicon = 'skbl'


# added as route in skblbackend.py
def get_places():
    size = 50000
    body = '{"aggs": {"places": {"terms": {"script_file": "place", "size": %s}}}}'\
           % (size)

    es = configM.elastic(lexicon=lexicon)
    index, typ = configM.get_lexicon_index(lexicon)
    ans = es.search(index=index, body=body, search_type="count")
    return ans['aggregations']['places']['buckets']


# added as route in skblbackend.py
def get_placenames():
    size = 50000
    body = '{"aggs": {"places": {"terms": {"script_file": "placename", "size": %s}}}}'\
           % (size)

    es = configM.elastic(lexicon=lexicon)
    index, typ = configM.get_lexicon_index(lexicon)
    ans = es.search(index=index, body=body, search_type="count")
    return ans['aggregations']['places']['buckets']


# This extra_src function (used in parser.py, called by configmanager.py) puts
# queries to skbl in lowercase.
# Always be case insensitive except for the meta fields
skbl_casesensitive = ["swoid", "id", "lexiconName", "resource", "lexiconOrder"]
def format_query(field, query):
    if field.split('.')[0] not in skbl_casesensitive:
        # don't change queries to the meta data fields
        return query.lower()
    else:
        return query
