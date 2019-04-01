import sys

import dotenv

dotenv.load_dotenv(dotenv_path=".env", verbose=True)

from karp5 import cli

if __name__ == "__main__":
    cli.cli_main(len(sys.argv), sys.argv)
