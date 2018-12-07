import io
from karp_backend.index import auto_update_es_doc
from karp_backend.server.translator.bulkify import bulkify


in_data = u"""[
    {"a": "test-1", "lexiconName": "test"},
    {"a": "test-2", "lexiconName": "test"}
]"""


@auto_update_es_doc('test')
def update_doc(doc, name, actiontype, user, date):
    doc['b'] = doc['a']


def test_bulkify():
    data = bulkify(in_data)
    assert isinstance(data, list)
    assert len(data) == 2
    for i, val in enumerate(data):
        assert 'b' in val['_source']
        assert val['_source']['b'] == 'test-{}'.format(i+1)
