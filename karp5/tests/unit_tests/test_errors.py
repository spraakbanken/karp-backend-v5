from karp5.errors import KarpException, KarpAuthenticationError, KarpQueryError, KarpGeneralError

from karp5.server.translator.errors import QueryError, AuthenticationError, BulkifyError


def test_KarpException_default():
    msg = "TEST"
    error = KarpException(msg)

    assert error.message == msg
    assert error.status_code == 400


def test_KarpException_status_code():
    msg = "TEST"
    error = KarpException(msg, status_code=800)

    assert error.message == msg
    assert error.status_code == 800


def test_KarpAuthenticationError_default():
    msg = "TEST"
    error = KarpAuthenticationError(msg)

    expected_message = f"Authentication Exception: {msg}"
    assert error.message == expected_message
    assert error.debug_msg == expected_message
    assert error.status_code == 401


def test_KarpAuthenticationError_status_code():
    msg = "TEST"
    error = KarpAuthenticationError(msg, status_code=800)

    expected_message = f"Authentication Exception: {msg}"
    assert error.message == expected_message
    assert error.debug_msg == expected_message
    assert error.status_code == 800


def test_KarpQueryError_default():
    msg = "TEST"
    error = KarpQueryError(msg)

    assert error.message == f"Query Error: {msg}. No query."


def test_KarpQueryError_query():
    msg = "TEST"
    query = "TEST_QUERY"
    error = KarpQueryError(msg, query=query)

    assert error.message == f"Query Error: {msg}. Query was '{query}'"


def test_KarpGeneralError_no_message():
    msg = None
    error = KarpGeneralError(msg)

    assert error.message == "Error: Unknown error."


def test_KarpGeneralError_message():
    msg = "TEST"
    error = KarpGeneralError(msg)

    assert error.message == f"Error: {msg}"


def test_QueryError():
    msg = "TEST"
    error = QueryError(msg)
    assert error.message == f"malformed query: {msg}"
    assert error.status_code == 400


def test_AuthenticationError():
    msg = "TEST"
    error = AuthenticationError(msg)

    assert error.message == f"Authentication Exception: {msg}"
    assert error.status_code == 401


def test_BulkifyError():
    msg = "TEST"
    bulk_info = "BULK_INFO_TEST"
    error = BulkifyError(msg, bulk_info)

    assert error.message == f"Bulkify error: {msg}\nbulk_info = {bulk_info}"
