# startup-scriptet (samma som strix har)
# TODO move to karp-backend-sb
from gevent import monkey
monkey.patch_all()
import sys
import json
from src.main_sb import app, load_urls
from gevent.pywsgi import WSGIServer

try:
    port = int(sys.argv[1])
except (IndexError, ValueError):
    sys.exit("Usage %s <port>" % sys.argv[0])
load_urls()
WSGIServer(('0.0.0.0', port), app).serve_forever()
