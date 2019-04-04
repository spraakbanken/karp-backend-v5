import six

from karp5 import config 


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
    
    
