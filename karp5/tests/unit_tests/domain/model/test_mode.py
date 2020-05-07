from karp5.domain.model.mode import Mode

MODE_DEFAULTS = {
    "elastic_url": ["http://elasticsearch:9200"],
    "sql": "karp",
    "type": "lexicalentry",
    "secret_fields": ["lastmodifiedBy"],
    "src": "",
    "suggestionalias": "karpsuggestion",
    "sort_by": ["lexiconOrder", "_score", "baseform.sort"],
    "head_sort_field": ["lexiconOrder"],
    "autocomplete_field": ["baseform"],
    "minientry_fields": ["lexiconName", "baseform", "baseform_en"],
    "statistics_buckets": ["lexiconName", "pos"],
    "boosts": ["baseform", "baseform_en"],
}


def test_mode_create_empty():
    mode = Mode(id="id", type="type", indexalias="indexalias", suggestionalias="suggestionalias")

    assert mode.id == "id"
    assert mode.elastic_url == []
    assert mode.sql is None
    assert mode.type == "type"
    assert mode.secret_fields == []
    assert mode.src is None
    assert mode.suggestionalias == "suggestionalias"
    assert mode.sort_by == []
    assert mode.head_sort_field == []
    assert mode.autocomplete_field == []
    assert mode.minientry_fields == []
    assert mode.statistics_buckets == []
    assert mode.boosts == []
    assert mode.is_index is False
    assert mode.indexalias == "indexalias"
    assert mode.groups == []
    assert mode.filter_for_unauth_user is None


def test_mode_create_from_dict_with_defaults():
    config = {
        "is_index": True,
        "indexalias": "large_lex",
        "secret_fields": [],
        "src": "",
        "suggestionalias": "barsuggestion",
        "sort_by": ["lexiconOrder", "_score", "foo.sort"],
        "head_sort_field": ["lexiconOrder"],
        "autocomplete_field": ["foo"],
        "minientry_fields": ["lexiconName", "foo"],
        "statistics_buckets": ["lexiconName", "foo"],
        "boosts": ["foo"],
    }
    mode = Mode.from_mapping(id="large_lex", mapping=config, defaults=MODE_DEFAULTS)

    assert mode.id == "large_lex"
    assert mode.elastic_url == MODE_DEFAULTS["elastic_url"]
    assert mode.sql == MODE_DEFAULTS["sql"]
    assert mode.type == MODE_DEFAULTS["type"]
    assert mode.secret_fields == config["secret_fields"]
    assert mode.src is None
    assert mode.suggestionalias == config["suggestionalias"]
    assert mode.sort_by == config["sort_by"]
    assert mode.head_sort_field == config["head_sort_field"]
    assert mode.autocomplete_field == config["autocomplete_field"]
    assert mode.minientry_fields == config["minientry_fields"]
    assert mode.statistics_buckets == config["statistics_buckets"]
    assert mode.boosts == config["boosts"]
    assert mode.is_index == config["is_index"]
    assert mode.indexalias == config["indexalias"]
    assert mode.groups == []
    assert mode.filter_for_unauth_user is None


def test_mode_create_from_dict_without_defaults():
    config = {
        "is_index": True,
        "indexalias": "large_lex",
        "secret_fields": [],
        "src": "",
        "suggestionalias": "barsuggestion",
        "sort_by": ["lexiconOrder", "_score", "foo.sort"],
        "head_sort_field": ["lexiconOrder"],
        "autocomplete_field": ["foo"],
        "minientry_fields": ["lexiconName", "foo"],
        "statistics_buckets": ["lexiconName", "foo"],
        "boosts": ["foo"],
        "type": "entry",
    }
    mode = Mode.from_mapping(id="large_lex", mapping=config)

    assert mode.id == "large_lex"
    assert mode.elastic_url == []
    assert mode.sql is None
    assert mode.type == config["type"]
    assert mode.secret_fields == config["secret_fields"]
    assert mode.src is None
    assert mode.suggestionalias == config["suggestionalias"]
    assert mode.sort_by == config["sort_by"]
    assert mode.head_sort_field == config["head_sort_field"]
    assert mode.autocomplete_field == config["autocomplete_field"]
    assert mode.minientry_fields == config["minientry_fields"]
    assert mode.statistics_buckets == config["statistics_buckets"]
    assert mode.boosts == config["boosts"]
    assert mode.is_index == config["is_index"]
    assert mode.indexalias == config["indexalias"]
    assert mode.groups == []
    assert mode.filter_for_unauth_user is None


def test_mode_create_changing_default_value_dont_changes_mode_defaults():
    config = {
        "is_index": True,
        "indexalias": "large_lex",
        "secret_fields": [],
        "src": "",
        "suggestionalias": "barsuggestion",
        "sort_by": ["lexiconOrder", "_score", "foo.sort"],
        "head_sort_field": ["lexiconOrder"],
        "autocomplete_field": ["foo"],
        "minientry_fields": ["lexiconName", "foo"],
        "statistics_buckets": ["lexiconName", "foo"],
        "boosts": ["foo"],
    }
    mode = Mode.from_mapping(id="large_lex", mapping=config, defaults=MODE_DEFAULTS)

    assert mode.elastic_url == MODE_DEFAULTS["elastic_url"]

    mode.elastic_url.append("added")

    assert mode.elastic_url == ["http://elasticsearch:9200", "added"]
    assert MODE_DEFAULTS["elastic_url"] == ["http://elasticsearch:9200"]


def test_mode_create_changing_mode_defaults_changes_values():
    config = {
        "is_index": True,
        "indexalias": "large_lex",
        "secret_fields": [],
        "src": "",
        "suggestionalias": "barsuggestion",
        "sort_by": ["lexiconOrder", "_score", "foo.sort"],
        "head_sort_field": ["lexiconOrder"],
        "autocomplete_field": ["foo"],
        "minientry_fields": ["lexiconName", "foo"],
        "statistics_buckets": ["lexiconName", "foo"],
        "boosts": ["foo"],
    }
    mode = Mode.from_mapping(id="large_lex", mapping=config, defaults=MODE_DEFAULTS)

    assert mode.elastic_url == MODE_DEFAULTS["elastic_url"]

    mode.secret_fields.append("added")

    assert mode.secret_fields == ["added"]
    assert config["secret_fields"] == ["added"]
