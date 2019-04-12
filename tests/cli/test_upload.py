import json
import time
try:
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from urllib import urlopen

import pytest

from karp5.cli import upload_offline as upload




def get_es_indices():
    url = 'http://127.0.0.1:9201/_cat/indices?format=json&h=health,index,docs.count'
    return json.loads(urlopen(url).read().decode('utf-8'))


def get_es_aliases():
    url = 'http://127.0.0.1:9201/_cat/aliases?format=json&h=alias,index'
    return json.loads(urlopen(url).read().decode('utf-8'))


def get_es_search(alias):
    url = 'http://127.0.0.1:9201/{}/_search'.format(alias)
    return json.loads(urlopen(url).read().decode('utf-8'))


def mk_indexname(mode, suffix):
    return '{}_{}'.format(mode, suffix)


def _test_index_exists(mode, suffix, n_docs):
    es_status = get_es_indices()
    print(es_status)
    index = mk_indexname(mode, suffix)
    for x in es_status:
        if x['index'] == index:
            assert x['health'] == 'yellow' or 'green'
            assert x['docs.count'] == n_docs
            break
    else:
        assert False, "Didn't find index '{}'".format(index)


def _test_alias_contains_index(mode, index):
    es_status = get_es_aliases()
    print(es_status)
    for x in es_status:
        if x['alias'] == mode:
            assert x['index'] == index
            break
    else:
        assert False, "Didn't find alias '{}'".format(mode)


def _test_n_hits_equals(mode, n_hits):
    es_hits = get_es_search(mode)
    print(es_hits)
    assert 'hits' in es_hits
    assert 'hits' in es_hits['hits']
    assert 'total' in es_hits['hits']
    assert es_hits['hits']['total'] == n_hits


def test_create_empty_index(cli_w_es):
    mode = 'panacea'
    suffix = 'test_upload_01'
    r = cli_w_es.create_empty_index(mode, suffix)

    assert r.exit_code == 0

    _test_index_exists(mode, suffix, '0')
    _test_n_hits_equals(mk_indexname(mode, suffix), 0)


def test_create_reindex_alias(cli_w_panacea):
    mode = 'panacea'
    suffix = 'test_upload_02'
    n_hits = 6609
    _test_n_hits_equals(mode, n_hits)
    r = cli_w_panacea.reindex_alias(mode, suffix)

    assert r.exit_code == 0

    _test_index_exists(mode, suffix, str(n_hits))

    r = cli_w_panacea.publish_mode(mode, suffix)
    assert r.exit_code == 0
    time.sleep(1)

    _test_alias_contains_index(mode, mk_indexname(mode, suffix))
    _test_alias_contains_index('karp', mk_indexname(mode, suffix))
    _test_alias_contains_index('panacea_links', mk_indexname(mode, suffix))
    _test_n_hits_equals(mode, n_hits)
    _test_n_hits_equals('karp', n_hits)
    _test_n_hits_equals('panacea_links', n_hits)


def test_copy_mode(cli_w_panacea):
    source_mode = 'panacea'
    target_mode = 'panacea_links'
    target_suffix = 'test_upload_03'
    n_hits = 6609
    ok, errors = upload.copy_alias_to_new_index(source_mode, target_mode, target_suffix)

    assert ok

    _test_index_exists(target_mode, target_suffix, n_hits)

    r = cli_w_panacea.publish_mode(target_mode, target_suffix)
    assert r.exit_code == 0
    time.sleep(1)

    _test_alias_contains_index(target_mode, mk_indexname(target_mode, target_suffix))
    _test_n_hits_equals(source_mode, n_hits)
    _test_n_hits_equals(target_mode, n_hits)


def test_copy_mode_w_query(cli_w_panacea):
    source_mode = 'panacea'
    target_mode = 'panacea_links'
    target_suffix = 'test_upload_04'
    source_n_hits = 6609
    target_n_hits = 1677
    query = '{ "query": { "term": { "pos": "Vb" } } }'
    ok, errors = upload.copy_alias_to_new_index(
        source_mode,
        target_mode,
        target_suffix,
        query=query
    )

    assert ok

    _test_index_exists(target_mode, target_suffix, target_n_hits)

    r = cli_w_panacea.publish_mode(target_mode, target_suffix)
    assert r.exit_code == 0
    time.sleep(1)

    _test_alias_contains_index(target_mode, mk_indexname(target_mode, target_suffix))
    _test_n_hits_equals(source_mode, n_hits)
    _test_n_hits_equals(target_mode, n_hits)


def do_update(lex, doc):
    doc['lex'] = lex
    return doc


def update_doc(m, doc):
    doc['x'] = do_update(m, doc['x'])
    return doc


def test_update_docs():
    mode = 'mode'
    docs = ({'id': i, 'x': {'v': i**2}}
            for i in range(10))
    upd = (update_doc(mode, x) for x in docs)

    for i, u in enumerate(upd):
        assert u['id'] == i
        assert u['x']['v'] == i**2
        assert u['x']['lex'] == mode

