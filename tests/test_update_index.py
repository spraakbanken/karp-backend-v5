import io
import json
from karp_backend.index import DocConverter
from karp_backend.index import doc_to_es
from karp_backend.index import doc_to_sql
from karp_backend.server.translator.bulkify import bulkify


in_data = u"""[
    {"a": "test-1", "lexiconName": "test"},
    {"a": "test-2", "lexiconName": "test"}
]"""


class UpdateDoc(DocConverter):
    LEXICONS = ['test']

    def to_es_doc(self, doc, name, actiontype, user, date):
        doc['b'] = doc['a']

    def to_sql_doc(self, doc, name, actiontype, user, date):
        if 'b' in doc:
            del doc['b']


def test_update_doc():
    docs = json.loads(in_data)
    for doc in docs:
        es_doc = doc_to_es(doc, 'test', 'add')
        assert 'b' in es_doc
        assert not 'b' in doc
        sql_doc = doc_to_sql(es_doc, 'test', 'add')
        assert not 'b' in sql_doc
        assert 'b' in es_doc


def test_bulkify():
    data = bulkify(in_data)
    assert isinstance(data, list)
    assert len(data) == 2
    for i, val in enumerate(data):
        assert 'b' in val['_source']
        assert val['_source']['b'] == 'test-{}'.format(i+1)
