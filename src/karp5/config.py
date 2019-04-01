import logging
import sys
import os.path
import time
import stat
import helper.configpaths as C

debugmode = C.config["DEBUG"]

today = time.strftime("%Y%m%d")
DEBUGFILE = os.path.join(debugmode["LOGDIR"], "%s-debug.txt" % today)


def debug_str_to_int(s):
    """
    Converting string to logging level. Case-insensitive.
    Defaults to logging level WARNING.

    :param s: the string to convert
    :returns: the corresponding logging.LEVEL if matching otherwise logging.WARNING
    """
    s_lower = s.lower()  # s.casefold() would be correct, but lower is sufficient
    # Setting logging.WARNING as default logging level
    debuglevel = logging.WARNING

    if s_lower == "debug":
        debuglevel = logging.DEBUG
    elif s_lower == "info":
        debuglevel = logging.INFO
    elif s_lower == "warning":
        debuglevel = logging.WARNING
    elif s_lower == "error":
        debuglevel = logging.ERROR
    elif s_lower == "critical":
        debuglevel = logging.CRITICAL
    else:
        print("NOTE: Can't match debuglevel in the config file.")
        print("NOTE: Using default level: WARNING.")
    return debuglevel


if debugmode["DEBUG_TO_STDERR"]:
    logging.basicConfig(
        stream=sys.stderr,
        level=debug_str_to_int(debugmode["DEBUGLEVEL"]),
        format=debugmode["LOGFMT"],
        datefmt=debugmode["DATEFMT"],
    )
else:
    # Create Logfile if it does not exist
    if not os.path.isfile(DEBUGFILE):
        with open(DEBUGFILE, "w") as f:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write("%s CREATED DEBUG FILE\n\n" % now)
        # Fix permissions
        os.chmod(
            DEBUGFILE,
            stat.S_IRUSR
            | stat.S_IRGRP
            | stat.S_IROTH
            | stat.S_IWUSR
            | stat.S_IWGRP
            | stat.S_IWOTH,
        )

    logging.basicConfig(
        filename=DEBUGFILE,
        level=debug_str_to_int(debugmode["DEBUGLEVEL"]),
        format=debugmode["LOGFMT"],
        datefmt=debugmode["DATEFMT"],
    )
