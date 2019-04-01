# import this to start up the logging, always have this line at the top of the file
import pkg_resources
import logging
import six

from .instance_info import get_instance_path


from flask import Flask

from .config import Config


__version__ = "5.8.0"
__name = "karp5"


def create_app(config_class=Config):
    app = Flask(__name, instance_path=get_instance_path())
    app.config.from_object(config_class)
    app.config.from_json("config/config.json")

    if not app.debug and not app.testing:
        logger = logging.getLogger("karp5")
        log_level = debug_str_to_int(app.config["DEBUG"]["DEBUGLEVEL"])
        logger.setLevel(log_level)
        formatter = logging.Formatter(fmt=app.config["DE"])

        if app.config["DEBUG"]["DEBUG_TO_STDERR"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)
            # logging.basicConfig(
            #    stream=sys.stderr,
            #    level=debug_str_to_int(debugmode['DEBUGLEVEL']),
            #    format=debugmode['LOGFMT'],
            #    datefmt=debugmode['DATEFMT']
            # )
            logger.addHandler(stream_handler)
    else:
        log_dir = app.config["DEBUG"]["LOGDIR"]
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler = logging.TimedRotatingFileHandler(
            os.path.join(log_dir, "karp5.log"), when="d", interval=1, backupCount=0
        )
        logger.addHandler(file_handler)
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

    return app


def get_version():
    return __version__


def get_name():
    return __name


def get_pkg_resource(filename):
    assert pkg_resources.resource_exists(__name__, filename)
    result = pkg_resources.resource_string(__name__, filename)
    if isinstance(result, six.binary_type):
        result = result.decode("utf-8")
    return result


# # import server.log
# from flask import Flask
#
# def create_app(app_path,
#                settings_override=None):
#     app = Flask('karp-backend', instance_path=app_path)
#
#     app.config.from_object('karp5.settings')
#     app.config.from_json('config/config.json', silent=True)
#     app.config.from_object(settings_override)
#
#     return app
#
# import logging
# logging.getLogger(__name__).addHandler(logging.NullHandler())
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
