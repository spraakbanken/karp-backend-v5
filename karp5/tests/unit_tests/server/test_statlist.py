"""Tests for statlist in karp5.server.searching"""
import json
from unittest import mock

from karp5.config import conf_mgr

import pytest

from karp5.server.searching import statlist


def test_statlist(app):
    # https://ws.spraakbanken.gu.se/ws/karp/stage/statlist?buckets=num_children.bucket,bostadsort.bucket&mode=skbl2&q=extended%7C%7Cand%7Canything%7Cequals%7Ctest&resource=skbl2&size=1000
    query = "/statlist?buckets=baseform.sort&mode=panacea&q=extended||and|anything|equals|test&size=1000"
    with app.test_request_context(query), mock.patch(
        "karp5.context.auth.validate_user", return_value=(True, ["skbl2"])
    ), mock.patch("karp5.server.searching.conf_mgr", return_value={}) as conf_mgr_mock, mock.patch(
        "karp5.server.searching.check_bucketsize", return_value={}
    ):
        conf_mgr_mock.get_mode_index.return_value = ("panacea", "entry")
        es_mock = mock.Mock()
        es_mock.search.return_value = {"aggregations": {"q_statistics": {}}}
        conf_mgr_mock.elastic.return_value = es_mock

        response = statlist()
        result = json.loads(response.get_data().decode("utf-8"))

    expected = {"is_more": {}, "stat_table": []}

    assert result == expected

