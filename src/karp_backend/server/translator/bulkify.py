""" Creates json annotated with metadata (index, type)
    that can be sent to elasticsearch
    Input: json structures that might be of type string ('{"hej" : "hu"}')
"""
from json import loads

from karp_backend.index import update_es_doc


_index = 'test'
_type = 'test'


def bulkify(data, bulk_info={}, with_id=False):
    """ parse a string with either a list or a single json object
        annotate with meta data
    """
    index = bulk_info.get('index', _index)
    itype = bulk_info.get('type', _type)
    items = loads(data)
    result = []
    for item in items:
        es_doc = item['_source'] if with_id else item
        update_es_doc(es_doc, es_doc['lexiconName'], 'bulk')
        doc = {
            '_index': index,
            '_type': itype,
            '_source': es_doc,
        }
        if with_id:
            doc['_id'] = es_doc['_id']
        result.append(doc)
    return result
    


def bulkify_sql(data, bulk_info={}):
    """ format a dictionary of ids mapped to sql objects into a bulk insert """
    index = bulk_info.get('index', _index)
    itype = bulk_info.get('type', _type)
    return [{'_index': index, '_type': itype, '_id': _id,
             '_source': item['doc']}
            for _id, item in data.items() if item['status'] != 'removed']
