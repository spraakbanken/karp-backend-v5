import sys

from karp5 import instance_info
from .config import Config
from karp.config import ConfigManager

# print(f"{instance_info.get_instance_path()}")
mgr = ConfigManager(instance_info.get_instance_path())

conf_mgr = mgr
