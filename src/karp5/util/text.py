BYTE_TYPES = (bytes, bytearray)
TEXT_TYPES = (str,)


def uton(x):
    return x


def ntob(x):
    return x.encode("utf-8", "surrogateescape")


def ntou(x):
    return x


def bton(x):
    return x.decode("utf-8", "surrogateescape")


ESCAPE_TM = dict((k, ntou(repr(chr(k))[1:-1])) for k in range(32))
ESCAPE_TM[0] = u"\0"
ESCAPE_TM[7] = u"\a"
ESCAPE_TM[8] = u"\b"
ESCAPE_TM[11] = u"\v"
ESCAPE_TM[12] = u"\f"
ESCAPE_TM[ord("\\")] = u"\\\\"


def escape_control(s):
    if isinstance(s, TEXT_TYPES):
        return s.translate(ESCAPE_TM)
    else:
        return (
            s.decode("utf-8", "surrogateescape")
            .translate(ESCAPE_TM)
            .encode("utf-8", "surrogateescape")
        )


def unescape_control(s):
    if isinstance(s, TEXT_TYPES):
        return s.encode("latin1", "backslashreplace").decode("unicode_escape")
    else:
        return (
            s.decode("utf-8", "surrogateescape")
            .encode("latin1", "backslashreplace")
            .decode("unicode_escape")
            .encode("utf-8", "surrogateescape")
        )


# Replace with a less hacky function? originally from:
# https://stackoverflow.com/questions/9778550/which-is-the-correct-way-to-encode-escape-characters-in-python-2-without-killing
# def control_escape(s):
# """ Escapes control characters so that they can be parsed by a json parser.
# Eg. '\u0001' => '\\u0001'
# Note that u'\u0001'.encode('unicode_escape') will encode the string as
#'\\x01', which do not work for json. Hence the .replace('\\x', '\u00').
# """
# the set of characters migth need to be extended
# if type(s) is not str and type(s) is not str:
#    s = str(s)
# control_chars = [chr(c) for c in range(0x20)]
# return u''.join([c.encode('unicode_escape').replace('\\x', '\u00')
#                if c in control_chars else c for c in s])
