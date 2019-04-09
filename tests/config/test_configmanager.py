import pytest
import six

from karp5 import config
from karp5.config import errors


def test_override_elastic_url():
    mgr = config.ConfigManager()
    elastic_url = 'test.elastic.url'

    for mode, mode_settings in six.viewitems(mgr.modes):
        assert 'elastic_url' in mode_settings
        assert mode_settings['elastic_url'] != elastic_url

    mgr.override_elastic_url(elastic_url)

    for mode, mode_settings in six.viewitems(mgr.modes):
        assert 'elastic_url' in mode_settings
        assert mode_settings['elastic_url'] == elastic_url


def test_config_for_test(app):
    assert config.mgr.app_config.DATABASE_BASEURL.startswith('sqlite')
    assert config.mgr.get_mode_sql('panacea').endswith('.db/karp')
    assert config.mgr.get_mode_sql('default').endswith('.db/karp')
    assert config.mgr.get_mode_sql('karp').endswith('.db/karp')


def test_real_config(real_app):
    assert config.mgr.app_config.DATABASE_BASEURL.startswith('mysql')


def test_get_mapping(app):
    mapping = config.mgr.get_mapping('panacea')
    assert isinstance(mapping, str)

    with pytest.raises(errors.KarpConfigException) as e:
        mapping = config.mgr.get_mapping('not-existing')
    assert "Can't find mappingconf for index 'not-existing'" in str(e.value)


@pytest.mark.parametrize('mode,facit',[
    ('panacea', ['panacea', 'karp'])
])
def test_get_modes_that_include_mode(app, mode, facit):
    modes = config.mgr.get_modes_that_include_mode(mode)
    assert len(modes) == len(facit)
    for m in modes:
        assert m in facit
    for f in facit:
        assert f in modes