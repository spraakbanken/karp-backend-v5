import os
import sys


def get_instance_path():
    if os.environ.get("KARP5_INSTANCE_PATH"):
        instance_path = os.path.abspath(os.environ.get("KARP5_INSTANCE_PATH"))
    else:
        instance_path = os.path.abspath(os.getcwd())
    print("INSTANCE_PATH = {}".format(instance_path), file=sys.stderr)
    # assert instance_path == None
    return instance_path


# def get_instance_path():
#     return instance_path
