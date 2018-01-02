import logging
import sys
import os.path
import time
import stat
import helper.configpaths as C

#debugmode = reload(debugmode)
debugmode = C.config['DEBUG']

today = time.strftime("%Y%m%d")
DEBUGFILE = os.path.join(debugmode['LOGDIR'], '%s-debug.txt' % today)

if debugmode['DEBUG_TO_STDERR']:
    logging.basicConfig(stream=sys.stderr, level=debugmode['DEBUGLEVEL'],
                        format=debugmode['LOGFMT'], datefmt=debugmode['DATEFMT'])
else:
    # Create Logfile if it does not exist
    if not os.path.isfile(DEBUGFILE):
        with open(DEBUGFILE, "w") as f:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write("%s CREATED DEBUG FILE\n\n" % now)
        # Fix permissions
        os.chmod(DEBUGFILE, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
                 stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    # TODO rewrite this stupid code
    if debugmode['DEBUGLEVEL'] == "DEBUG":
        debuglevel = logging.DEBUG
    if debugmode['DEBUGLEVEL'] == "INFO":
        debuglevel = logging.INFO
    if debugmode['DEBUGLEVEL'] == "WARNING":
        debuglevel = logging.WARNING
    if debugmode['DEBUGLEVEL'] == "ERROR":
        debuglevel = logging.ERROR
    if debugmode['DEBUGLEVEL'] == "CRITICAL":
        debuglevel = logging.CRITICAL

    logging.basicConfig(filename=DEBUGFILE, level=debuglevel,
                        format=debugmode['LOGFMT'], datefmt=debugmode['DATEFMT'])
