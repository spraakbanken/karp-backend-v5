from karp5 import instance_info
from .config import Config
from .configmanager import ConfigManager

mgr = ConfigManager(instance_info.get_instance_path())

conf_mgr = mgr
