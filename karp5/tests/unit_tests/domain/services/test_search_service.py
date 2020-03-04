from unittest import mock

import pytest

import elasticsearch_dsl as es_dsl

from karp5.domain.services import search_service


@pytest.mark.parametrize(
    "from_,size,expected_calls",
    [
        # (None, None, [mock.call.extra(from_=0, size=0), mock.call.execute().to_dict()]),
        (
            0,
            25,
            [
                mock.call.extra(size=25),
                mock.call.extra().execute(),
                mock.call.extra().execute().to_dict(),
            ],
        ),
        (
            0,
            25,
            [
                mock.call.extra(from_=0, size=25),
                mock.call.extra().execute(),
                mock.call.extra().execute().to_dict(),
            ],
        ),
    ],
)
def test_execute_query_execute(from_, size, expected_calls):
    scan_limit = 1000
    es_search_mock = mock.Mock(name="es_search", spec=es_dsl.Search)
    # es_search_params_mock = mock.Mock(name="es_search_params", spec=es_dsl.Search)
    # es_search_mock.params.return_value = es_search_params_mock
    # es_search_params_mock.scan.return_value = []
    with mock.patch("karp5.config.conf_mgr") as conf_mgr_mock:
        conf_mgr_mock.app_config.return_value.SCAN_LIMIT = scan_limit
        # conf_mgr_mock.__getitem__.return_value = conf_mgr_mock
        search_service.execute_query(es_search_mock, from_=from_, size=size)

    # assert es_search_mock.mock_calls == expected_calls


@pytest.mark.parametrize(
    "from_,size,expected_calls",
    [
        (
            5,
            1200,
            [
                mock.call.extra(from_=0, size=0),
                mock.call.extra().execute(),
                mock.call.params(preserve_order=True, scroll="5m"),
            ],
        ),
    ],
)
def test_execute_query_scan(from_, size, expected_calls):
    scan_limit = 1000
    es_search_mock = mock.Mock(name="es_search", spec=es_dsl.Search)
    es_search_params_mock = mock.Mock(name="es_search_params", spec=es_dsl.Search)
    es_search_mock.params.return_value = es_search_params_mock
    es_search_params_mock.scan.return_value = []
    with mock.patch("karp5.config.conf_mgr") as conf_mgr_mock:
        conf_mgr_mock.app_config.return_value.SCAN_LIMIT = scan_limit
        # conf_mgr_mock.__getitem__.return_value = conf_mgr_mock
        search_service.execute_query(es_search_mock, from_=from_, size=size)

    # assert es_search_mock.mock_calls == expected_calls
    # assert es_search_params_mock.mock_calls == [mock.call.scan()]
