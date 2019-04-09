from __future__ import unicode_literals
# startup-scriptet (samma som strix har)
# TODO move to karp-backend-sb
#from gevent import monkey
#monkey.patch_all()
import sys
import json

import dotenv
dotenv.load_dotenv(dotenv_path='.env', verbose=True)

import karp5
#from gevent.pywsgi import WSGIServer

def main_wsgi():
    try:
        port = int(sys.argv[1])
    except (IndexError, ValueError):
        sys.exit("Usage %s <port>" % sys.argv[0])
    app = karp5.create_app()
    WSGIServer(('0.0.0.0', port), app).serve_forever()

def main_debug():
    app = karp5.create_app()
    app.run()

if __name__ == '__main__':
    main_debug()
    