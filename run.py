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



if __name__ == '__main__':
    arg = sys.argv[1]
    app = karp5.create_app()
    if arg == 'dev':
        app.run(debug=True, port=8081)
    else:
        try:
            port = int(arg)
        except (IndexError, ValueError):
            sys.exit("Usage %s <port>" % sys.argv[0])

        WSGIServer(('0.0.0.0', port), app).serve_forever()
