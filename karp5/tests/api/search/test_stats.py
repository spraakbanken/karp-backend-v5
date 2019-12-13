import json

import pytest


def get_json(client, path):
    print("Calling '{}' ...".format(path))
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return json.loads(response.data.decode())


@pytest.mark.parametrize(
    "query_string,n_hits",
    [
        (None, 6609),
        ("q=simple||sit&mode=panacea", 2),
        ("q=simple||sit&mode=karp", 2),
        ("resource=panacea&mode=karp", 6609),
        ("mode=karp", 6609),
        ("mode=panacea", 6609),
        ("q=simple||sit", 2),
        ("q=extended||and|pos|exists&mode=panacea", 6609),
        ("q=extended||and|pos|missing&mode=panacea", 0),
        ("q=extended||and|baseform|startswith|ang&mode=panacea", 22),
        ("q=extended||and|baseform|startswith|ang|be&mode=panacea", 422),
        ("q=extended||and|pos|equals|Vb||and|baseform|startswith|ab&mode=panacea", 65),
        ("q=extended||and|baseform_en|regexp|s.*t&mode=panacea", 313),
        (
            "q=extended||and|pos|equals|Vb||not|baseform|startswith|ab&mode=panacea",
            1612,
        ),
        ("buckets=lexiconName.bucket,baseform.sort&size=200", 6609),
    ],
)
def test_statistics(client_w_panacea, query_string, n_hits):
    query = "/statistics"
    if query_string:
        query = query + "?" + query_string

    result = get_json(client_w_panacea, query)

    assert "aggregations" in result
    # if n_hits == 0:
    #     assert len(result['aggregations']) == 0
    # else:
    assert result["aggregations"]["q_statistics"]["doc_count"] == n_hits
    if n_hits > 0:
        assert (
            len(result["aggregations"]["q_statistics"]["lexiconName"]["buckets"]) == 1
        )
        assert (
            result["aggregations"]["q_statistics"]["lexiconName"]["buckets"][0][
                "doc_count"
            ]
            == n_hits
        )
        assert (
            result["aggregations"]["q_statistics"]["lexiconName"]["buckets"][0]["key"]
            == "panacea"
        )
    else:
        assert (
            len(result["aggregations"]["q_statistics"]["lexiconName"]["buckets"]) == 0
        )
