import os

os.environ["KARP5_INSTANCE_PATH"] = os.path.join(os.path.dirname(__file__), "../../../karp5/tests/data/")
assert os.environ["KARP5_INSTANCE_PATH"] == os.path.join(os.path.dirname(__file__), "../../../karp5/tests/data/")
print(os.environ["KARP5_INSTANCE_PATH"])