""" Creates json annotated with metadata (index, type)
    that can be sent to elasticsearch
    Input: json structures that might be of type string ('{"hej" : "hu"}')
"""
import json

from karp5.document import doc_to_es

# from karp5.document import doc_to_sql


_index = "test"
_type = "test"


def bulkify(data, bulk_info={}, with_id=False):
    """ parse a string with either a list or a single json object
        annotate with meta data
    """
    index = bulk_info.get("index", _index)
    itype = bulk_info.get("type", _type)
    items = json.loads(data)
    result = []
    for item in items:
        data_doc = item["_source"] if with_id else item
        # assert 'lexiconName' in data_doc, "document doesn't have the field 'lexiconName'"
        es_doc = doc_to_es(data_doc, data_doc["lexiconName"], "bulk")
        doc = {
            "_index": index,
            "_type": itype,
            "_source": es_doc,
        }
        if with_id:
            doc["_id"] = item["_id"]
        result.append(doc)
    return result


def bulkify_sql(data, bulk_info={}):
    """ format a dictionary of ids mapped to sql objects into a bulk insert """
    index = bulk_info.get("index", _index)
    itype = bulk_info.get("type", _type)
    return [
        {"_index": index, "_type": itype, "_id": _id, "_source": item["doc"]}
        for _id, item in list(data.items())
        if item["status"] != "removed"
    ]
    # result = []
    # for _id, item in list(data.items()):
    #     if item["status"] != "removed":
    #         data_doc = item["doc"]
    #         es_doc = doc_to_es(data_doc, data_doc["lexiconName"], "bulk")
    #         doc = {"_index": index, "_type": itype, "_source": es_doc, "_id": _id}
    #         result.append(doc)
    # return result
