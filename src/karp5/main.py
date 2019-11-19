# -*- coding: utf-8 -*-

import karp5


def main():
    app = karp5.create_app()
    app.run(port=8081, debug=True)


if __name__ == "__main__":
    main()
