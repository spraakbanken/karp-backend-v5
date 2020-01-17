import json
import time
import os

try:
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from urllib import urlopen
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

# import elasticsearch_dsl as es_dsl
import pytest

from karp5.cli import upload_offline as upload


def get_es_indices():
    url = "http://127.0.0.1:9201/_cat/indices?format=json&h=health,index,docs.count"
    return json.loads(urlopen(url).read().decode("utf-8"))


def get_es_aliases():
    url = "http://127.0.0.1:9201/_cat/aliases?format=json&h=alias,index"
    return json.loads(urlopen(url).read().decode("utf-8"))


def get_es_search(alias):
    url = "http://127.0.0.1:9201/{}/_search".format(alias)
    return json.loads(urlopen(url).read().decode("utf-8"))


def mk_indexname(mode, suffix):
    return "{}_{}".format(mode, suffix)


def _test_index_exists(mode, suffix, n_docs):
    if isinstance(n_docs, int):
        n_docs = str(n_docs)
    es_status = get_es_indices()
    print(es_status)
    index = mk_indexname(mode, suffix)
    for index_status in es_status:
        if index_status["index"] == index:
            assert index_status["health"] == "yellow" or "green"
            assert index_status["docs.count"] == n_docs
            break
    else:
        assert False, "Didn't find index '{}'".format(index)


def _test_alias_contains_index(alias, index):
    es_status = get_es_aliases()
    print(es_status)
    for x in es_status:
        if x["alias"] == alias and x["index"] == index:
            break
    else:
        assert False, "Didn't find index '{}' in alias '{}'".format(index, alias)


def _test_n_hits_equals(mode, n_hits):
    es_hits = get_es_search(mode)
    print(es_hits)
    assert "hits" in es_hits
    assert "hits" in es_hits["hits"]
    assert "total" in es_hits["hits"]
    assert es_hits["hits"]["total"] == n_hits


def test_create_empty_index(cli_w_es):
    mode = "panacea"
    suffix = "test_upload_01"
    r = cli_w_es.create_empty_index(mode, suffix)

    assert r.exit_code == 0

    _test_index_exists(mode, suffix, "0")
    _test_n_hits_equals(mk_indexname(mode, suffix), 0)
    assert upload.index_exists(mode, mk_indexname(mode, suffix))


def test_lexicon_init(cli_w_es):
    mode = "foo"
    lexicon = "bar"
    suffix = "test_init_01"
    result = cli_w_es.lexicon_init(lexicon, suffix)

    assert result.exit_code == 0

    time.sleep(5)
    _test_index_exists(mode, suffix, 3)

    filename = os.path.join("karp5", "tests", "data", "data", "custom_path_bar.json")
    result = cli_w_es.lexicon_init(lexicon, suffix, data=filename)

    assert result.exit_code == 0

    time.sleep(5)
    _test_index_exists(mode, suffix, 5)


def test_create_reindex_alias(cli_w_panacea):
    mode = "panacea"
    suffix = "test_upload_02"
    n_hits = 6609
    _test_n_hits_equals(mode, n_hits)
    r = cli_w_panacea.reindex_alias(mode, suffix)

    assert r.exit_code == 0

    time.sleep(10)
    _test_index_exists(mode, suffix, str(n_hits))

    r = cli_w_panacea.publish_mode(mode, suffix)
    assert r.exit_code == 0
    time.sleep(10)

    _test_alias_contains_index(mode, mk_indexname(mode, suffix))
    _test_alias_contains_index("karp", mk_indexname(mode, suffix))
    _test_alias_contains_index("panacea_links", mk_indexname(mode, suffix))
    _test_n_hits_equals(mode, n_hits)
    _test_n_hits_equals("karp", n_hits)
    _test_n_hits_equals("panacea_links", n_hits)


def test_copy_mode(cli_w_panacea):
    source_mode = "panacea"
    target_mode = "panacea_links"
    target_suffix = "test_upload_03"
    n_hits = 6609
    _test_n_hits_equals(source_mode, n_hits)
    ok, errors = upload.copy_alias_to_new_index(source_mode, target_mode, target_suffix)

    assert ok
    assert errors is None

    time.sleep(5)
    _test_index_exists(target_mode, target_suffix, n_hits)

    r = cli_w_panacea.publish_mode(target_mode, target_suffix)
    assert r.exit_code == 0
    time.sleep(5)

    _test_alias_contains_index(target_mode, mk_indexname(target_mode, target_suffix))
    _test_n_hits_equals(source_mode, n_hits)
    _test_n_hits_equals(mk_indexname(target_mode, target_suffix), n_hits)
    _test_n_hits_equals(target_mode, 2 * n_hits)


def test_copy_mode_w_query(cli_w_panacea):
    source_mode = "panacea"
    target_mode = "panacea_links"
    target_suffix = "test_upload_04"
    source_n_hits = 6609
    target_n_hits = 1677
    query = {"query": {"match": {"pos_german": "Vb"}}}
    # query = es_dsl.Q('match', pos='Vb')
    _test_n_hits_equals(source_mode, source_n_hits)
    ok, errors = upload.copy_alias_to_new_index(
        source_mode, target_mode, target_suffix, query=query
    )

    assert ok
    assert errors is None

    time.sleep(5)
    _test_index_exists(target_mode, target_suffix, target_n_hits)

    r = cli_w_panacea.publish_mode(target_mode, target_suffix)
    assert r.exit_code == 0
    time.sleep(5)

    _test_alias_contains_index(target_mode, mk_indexname(target_mode, target_suffix))
    _test_n_hits_equals(source_mode, source_n_hits)
    _test_n_hits_equals(mk_indexname(target_mode, target_suffix), target_n_hits)
    _test_n_hits_equals(target_mode, source_n_hits + target_n_hits)


def mock_copy_alias(source_docs, lex, filter_func=None):
    if filter_func:
        source_docs = upload.apply_filter(source_docs, filter_func)

    def update_doc(doc):
        doc["_source"]["lexicon"] = lex
        return doc

    updated_docs = (update_doc(doc) for doc in source_docs)

    return updated_docs


def gen_data(n):
    for i in range(1, n):
        yield {"_source": {"id": i}, "_id": i + 4321}


def filter_even_gen(doc, _id):
    if doc["id"] % 2 == 0:
        yield doc
        c = doc.copy()
        c["link"] = c["id"]
        c["id"] = c["id"] + 100
        yield c


def filter_even_list(doc, _id):
    result = []
    if doc["id"] % 2 == 0:
        c = doc.copy()
        c["link"] = c["id"]
        c["id"] = c["id"] + 100
        result.append(c)
    return result


@pytest.mark.parametrize(
    "gen,lex,filter_func,expected",
    [
        (gen_data(10), "lex", None, gen_data(10)),
        (
            gen_data(10),
            "lex",
            filter_even_gen,
            [
                {"_source": {"id": 2}},
                {"_source": {"id": 102, "link": 2}},
                {"_source": {"id": 4}},
                {"_source": {"id": 104, "link": 4}},
                {"_source": {"id": 6}},
                {"_source": {"id": 106, "link": 6}},
                {"_source": {"id": 8}},
                {"_source": {"id": 108, "link": 8}},
            ],
        ),
        (
            gen_data(10),
            "lex",
            filter_even_list,
            [
                {"_source": {"id": 102, "link": 2}},
                {"_source": {"id": 104, "link": 4}},
                {"_source": {"id": 106, "link": 6}},
                {"_source": {"id": 108, "link": 8}},
            ],
        ),
    ],
)
def test_apply_filter(gen, lex, filter_func, expected):
    docs = mock_copy_alias(gen, lex, filter_func)

    for x, f in zip_longest(docs, expected):
        assert x is not None
        assert f is not None

        assert x["_source"]["id"] == f["_source"]["id"]
        assert x["_source"]["lexicon"] == lex


def test_recover(cli_w_panacea):
    alias = "panacea"
    alias_hits = get_es_search(alias)

    suffix = "test_recover"
    assert upload.recover(alias, suffix, alias)

    time.sleep(3)
    recover_hits = get_es_search(mk_indexname(alias, suffix))

    assert "hits" in alias_hits
    assert "hits" in alias_hits["hits"]
    assert "total" in alias_hits["hits"]

    assert "hits" in recover_hits
    assert "hits" in recover_hits["hits"]
    assert "total" in recover_hits["hits"]

    assert alias_hits["hits"]["total"] == recover_hits["hits"]["total"]
