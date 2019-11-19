
import dotenv

dotenv.load_dotenv(dotenv_path=".env", verbose=True)

from karp5 import cli

if __name__ == "__main__":
    cli.setup_cli()
    cli.cli()
