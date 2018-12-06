import json
import os

from ..instance_info import get_instance_path


# configdir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config')

configdir = os.path.join(get_instance_path(), 'config')

with open(os.path.join(configdir, 'modes.json')) as fp:
    searchconfig = json.load(fp)

with open(os.path.join(configdir, 'lexiconconf.json')) as fp:
    lexiconconfig = json.load(fp)
with open(os.path.join(configdir, 'config.json')) as fp:
    config = json.load(fp)
with open(os.path.join(configdir, 'mappings/fieldmappings_default.json')) as fp:
    defaultfields = json.load(fp)
