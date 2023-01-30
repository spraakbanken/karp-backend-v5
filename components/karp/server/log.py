import logging
import sys
import os.path
import time
import stat
from config import debugmode
import importlib

debugmode = importlib.reload(debugmode)

today = time.strftime("%Y%m%d")
DEBUGFILE = os.path.join(debugmode.LOGDIR, '%s-debug.txt' % today)

if debugmode.DEBUG_TO_STDERR:
    logging.basicConfig(stream=sys.stderr, level=debugmode.DEBUGLEVEL,
                        format=debugmode.LOGFMT, datefmt=debugmode.DATEFMT)
else:
    # Create Logfile if it does not exist
    if not os.path.isfile(DEBUGFILE):
        with open(DEBUGFILE, "w") as f:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write("%s CREATED DEBUG FILE\n\n" % now)
        # Fix permissions
        os.chmod(DEBUGFILE, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
                 stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    logging.basicConfig(filename=DEBUGFILE, level=debugmode.DEBUGLEVEL,
                        format=debugmode.LOGFMT, datefmt=debugmode.DATEFMT)
