""" Creates json annotated with metadata (index, type)
    that can be sent to elasticsearch
    Input: json structures that might be of type string ('{"hej" : "hu"}')
"""
from json import loads
_index = 'test'
_type = 'test'


def bulkify(data, bulk_info={}, with_id=False):
    """ parse a string with either a list or a single json object
        annotate with meta data
    """
    index = bulk_info.get('index', _index)
    itype = bulk_info.get('type', _type)
    items = loads(data)
    if with_id:
        return [{'_index': index, '_type': itype, '_source': item['_source'],
                 '_id': item['_id']} for item in items]

    return [{'_index': index, '_type': itype, '_source': item}
            for item in items]


def bulkify_sql(data, bulk_info={}):
    """ format a dictionary of ids mapped to sql objects into a bulk insert """
    index = bulk_info.get('index', _index)
    itype = bulk_info.get('type', _type)
    return [{'_index': index, '_type': itype, '_id': _id,
             '_source': item['doc']}
            for _id, item in data.items() if item['status'] != 'removed']
