def test_cli_recover(cli_w_foo):
    mode = "foo"
    lexicon = "foo"
    suffix = "test_cli_recover"

    r = cli_w_foo.recover_mode(mode, lexicons=[lexicon], suffix=suffix)

    assert r.exit_code == 0
