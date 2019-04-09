from __future__ import unicode_literals
from builtins import object
import json
import os
import six

from karp5.instance_info import get_instance_path

# configdir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config')
class LazyJsonLoader(object):
    def __init__(
            self,
            path,
            # *,
            setup_func = None
        ):
        self.path = path
        self.setup_func = setup_func
        self.data = None

    def __getitem__(self, key):
        if not self.data:
            self._load_data()

        return self.data[key]

    def __setitem__(self, key, value):
        if not self.data:
            self._load_data()

        self.data[key] = value

    def _load_data(self):
        with open(self.path) as fp:
            self.data = json.load(fp)

        assert self.data is not None

        if self.setup_func:
            self.setup_func(self.data)


def set_defaults(data):
    defaults = data.get('default', None)
    if not defaults:
        return
    for data_key, data_val in six.viewitems(data):
        if data_key != 'default':
            for def_key, def_val in six.viewitems(defaults):
                if def_key not in data_val:
                    data_val[def_key] = def_val


configdir = os.path.join(get_instance_path(), 'config')

searchconfig = LazyJsonLoader(
    os.path.join(configdir, 'modes.json'),
    setup_func = set_defaults
)

lexiconconfig = LazyJsonLoader(
    os.path.join(configdir, 'lexiconconf.json'),
    setup_func = set_defaults
)

config = LazyJsonLoader(
    os.path.join(configdir, 'config.json')
)

defaultfields = LazyJsonLoader(
    os.path.join(configdir, 'mappings/fieldmappings_default.json')
)
