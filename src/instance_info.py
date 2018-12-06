import os


instance_path = os.path.abspath(os.environ.get('KARP_INSTANCE_PATH'))


def get_instance_path():
    return instance_path
