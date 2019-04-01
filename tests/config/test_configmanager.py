import six

from karp5.server.helper.configmanager import ConfigManager


def test_override_elastic_url():
    mgr = ConfigManager()
    elastic_url = 'test.elastic.url'

    for mode, mode_settings in six.viewitems(mgr.searchconfig):
        assert 'elastic_url' in mode_settings
        assert mode_settings['elastic_url'] != elastic_url

    mgr.override_elastic_url(elastic_url)

    for mode, mode_settings in six.viewitems(mgr.searchconfig):
        assert 'elastic_url' in mode_settings
        assert mode_settings['elastic_url'] == elastic_url
