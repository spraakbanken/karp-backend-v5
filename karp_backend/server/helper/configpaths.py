import json
import os

configdir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config')

searchconfig = json.load(open(os.path.join(configdir, 'modes.json')))
lexiconconfig = json.load(open(os.path.join(configdir, 'lexiconconf.json')))
config = json.load(open(os.path.join(configdir, 'config.json')))
defaultfields = json.load(open(os.path.join(configdir, 'mappings/fieldmappings_default.json')))
