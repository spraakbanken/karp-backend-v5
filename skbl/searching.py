import src.server.helper.configmanager as configM


lexicon = 'skbl'


def get_places():
    size = 50000
    body = '{"aggs": {"places": {"terms": {"script_file": "place", "size": %s}}}}'\
           % (size)

    es = configM.elastic(lexicon=lexicon)
    index, typ = configM.get_lexicon_index(lexicon)
    ans = es.search(index=index, body=body, search_type="count")
    return ans['aggregations']['places']['buckets']


def get_placenames():
    size = 50000
    body = '{"aggs": {"places": {"terms": {"script_file": "placename", "size": %s}}}}'\
           % (size)

    es = configM.elastic(lexicon=lexicon)
    index, typ = configM.get_lexicon_index(lexicon)
    ans = es.search(index=index, body=body, search_type="count")
    return ans['aggregations']['places']['buckets']
