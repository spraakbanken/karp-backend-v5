import os

import pytest

from karp5 import conf_mgr, config
from karp5.instance_info import get_instance_path
from karp5.config import errors


def test_override_elastic_url():
    mgr = config.ConfigManager("path")
    elastic_url = "test.elastic.url"

    for mode, mode_settings in mgr.modes.items():
        assert "elastic_url" in mode_settings
        assert mode_settings["elastic_url"] != elastic_url

    mgr.override_elastic_url(elastic_url)

    for mode, mode_settings in mgr.modes.items():
        assert "elastic_url" in mode_settings
        assert mode_settings["elastic_url"] == elastic_url


def test_config_for_test(app):
    assert conf_mgr.app_config.OVERRIDE_ELASTICSEARCH_URL
    if os.environ.get("KARP5_DBPASS"):
        assert conf_mgr.app_config.DATABASE_BASEURL.startswith("mysql")
    else:
        assert conf_mgr.app_config.DATABASE_BASEURL.startswith("sqlite")
    assert conf_mgr.get_mode_sql("panacea") is not None
    assert conf_mgr.get_mode_sql("default") is not None
    assert conf_mgr.get_mode_sql("karp") is not None


# def test_real_config(real_app):
#     assert config.mgr.app_config.DATABASE_BASEURL.startswith('mysql')


def test_get_mapping(app):
    mapping = config.mgr.get_mapping("panacea")
    assert isinstance(mapping, str)

    with pytest.raises(errors.KarpConfigException) as e:
        mapping = config.mgr.get_mapping("not-existing")
    assert "Can't find mappingconf for index 'not-existing'" in str(e.value)


def test_default_filename(app):
    lexicon = "foo"
    filename = conf_mgr.default_filename(lexicon)

    assert filename == os.path.join(os.path.abspath(get_instance_path()), "data", "foo", "foo.json")


@pytest.mark.parametrize("mode,facit", [("panacea", ["panacea", "karp", "panacea_links"])])
def test_get_modes_that_include_mode(app, mode, facit):
    modes = config.mgr.get_modes_that_include_mode(mode)
    assert len(modes) == len(facit)
    for m in modes:
        assert m in facit
    for f in facit:
        assert f in modes


@pytest.mark.parametrize("mode,expected", [("karp", None), ("foo", {"status": "ok"}),])
def test_filter_for_unauth_user(app, mode, expected):
    assert conf_mgr.filter_for_unauth_user(mode) == expected


def test_lookup_multiple_score(app):
    mode = "panacea"
    result = conf_mgr.lookup_multiple("_score", mode)
    expected = ["_score"]

    assert result == expected
