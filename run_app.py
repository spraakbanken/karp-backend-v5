from __future__ import unicode_literals
# startup-scriptet (samma som strix har)
# TODO move to karp-backend-sb
#from gevent import monkey
#monkey.patch_all()
import sys
import json

import dotenv
dotenv.load_dotenv(dotenv_path='.env', verbose=True)

import app
#from gevent.pywsgi import WSGIServer

#try:
#    port = int(sys.argv[1])
#except (IndexError, ValueError):
#    sys.exit("Usage %s <port>" % sys.argv[0])

app = app.create_app()

if __name__ == '__main__':
    app.run()

# WSGIServer(('0.0.0.0', port), app).serve_forever()
