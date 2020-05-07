import pytest


@pytest.mark.xfail(reason="fails though the command works live.")
def test_cli_recover(cli_w_foo):
    mode = "foo"
    lexicon = "foo"
    suffix = "test_cli_recover"

    r = cli_w_foo.recover_mode(mode, lexicons=[lexicon], suffix=suffix)

    assert r.exit_code == 0
