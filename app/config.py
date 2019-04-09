from __future__ import unicode_literals
from builtins import object
import os

if os.environ.get('KARP_INSTANCE_PATH'):
    instance_path = os.path.abspath(os.environ.get('KARP_INSTANCE_PATH'))
else:
    instance_path = os.path.abspath(__file__)

print("INSTANCE_PATH = {}".format(instance_path))


def get_instance_path():
    return instance_path


class Config(object):
    LOG_TO_STDOUT = True
