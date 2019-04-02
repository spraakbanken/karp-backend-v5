import six

from karp5 import config 


def test_override_elastic_url():
    mgr = config.ConfigManager()
    elastic_url = 'test.elastic.url'

    for mode, mode_settings in six.viewitems(mgr.searchconfig):
        assert 'elastic_url' in mode_settings
        assert mode_settings['elastic_url'] != elastic_url

    mgr.override_elastic_url(elastic_url)

    for mode, mode_settings in six.viewitems(mgr.searchconfig):
        assert 'elastic_url' in mode_settings
        assert mode_settings['elastic_url'] == elastic_url


def test_config_for_test(app):
    assert config.mgr.app_config.DATABASE_BASEURL.startswith('sqlite')


def test_real_config(real_app):
    assert config.mgr.app_config.DATABASE_BASEURL.startswith('mysql')
    
    
