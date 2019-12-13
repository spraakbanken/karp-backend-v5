from karp5.config.errors import KarpConfigException


def test_msg():
    msg = "test"
    e = KarpConfigException(msg)

    assert e.message == msg


def test_msg_fmt_1_arg():
    msg_fmt = "test '%s'"
    msg_var = "test"
    e = KarpConfigException(msg_fmt, msg_var)

    assert e.message == (msg_fmt % msg_var)


def test_msg_fmt_2_args():
    msg_fmt = "test '%s' '%s'"
    msg_var_1 = "one"
    msg_var_2 = "two"
    e = KarpConfigException(msg_fmt, msg_var_1, msg_var_2)

    assert e.message == (msg_fmt % (msg_var_1, msg_var_2))


def test_msg_fmt_2_args_w_debug_msg():
    msg_fmt = "test '%s' '%s'"
    msg_var_1 = "one"
    msg_var_2 = "two"
    debug_msg = "test debug"
    e = KarpConfigException(msg_fmt, msg_var_1, msg_var_2, debug_msg=debug_msg)

    assert e.message == (msg_fmt % (msg_var_1, msg_var_2))
    assert e.debug_msg == debug_msg

