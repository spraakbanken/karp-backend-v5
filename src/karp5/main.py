# -*- coding: utf-8 -*-
import server.helper.flaskhelper as flaskhelper
import karp5.backend as backend


def load_urls():
    flaskhelper.register(backend.init)


app = flaskhelper.app

if __name__ == '__main__':
    load_urls()
    flaskhelper.app.run()
