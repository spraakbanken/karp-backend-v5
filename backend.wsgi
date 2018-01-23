import sys
import os

project_name = ''
project_dir = os.path.join(os.path.dirname(__file__), project_name)

# Uncomment if using without docker
# activate_this = os.path.join(project_dir, 'venv/bin/activate_this.py')
# execfile(activate_this, dict(__file__=activate_this))

if project_dir not in sys.path:
    sys.path.append(project_dir)

from src.main import app as real_application, load_urls
import src.server.helper.configmanager as configM

load_urls()


def application(env, resp):
    env['SCRIPT_NAME'] = configM.setupconfig['SCRIPT_PATH']
    return real_application(env, resp)
