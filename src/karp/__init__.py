# import this to start up the logging, always have this line at the top of the file
# import server.log
from flask import Flask

def create_app(app_path,
               settings_override=None):
    app = Flask('karp-backend', instance_path=app_path)

    app.config.from_object('karp_backend.settings')
    app.config.from_json('config/config.json', silent=True)
    app.config.from_object(settings_override)

    return app

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
