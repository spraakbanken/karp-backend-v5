import sys
import os

project_name = ''
project_dir = os.path.join(os.path.dirname(__file__), project_name)

activate_this = os.path.join(project_dir, 'venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

if project_dir not in sys.path:
    sys.path.append(project_dir)

# from backend import app as real_application
# import config.setup as conf
from src.main_sb import app as real_application, load_urls
import config.setup as conf

load_urls()

def application(env, resp):
    env['SCRIPT_NAME'] = conf.script_path
    return real_application(env, resp)
