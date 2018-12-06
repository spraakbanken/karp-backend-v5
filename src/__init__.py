# import this to start up the logging, always have this line at the top of the file
import server.log
from instance_info import get_instance_path


from flask import Flask


def create_app(name, instance_path):
    app = Flask(name, instance_path=get_instance_path())

    return app
