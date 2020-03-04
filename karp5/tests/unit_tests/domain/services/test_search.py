from unittest import mock

import pytest

from karp5.domain.services import search


def test_execute_query():
    from_ = 0
    size = 0
    query = {}

    result = search.execute_query()
