# -*- coding: utf-8 -*-
import src.server.helper.flaskhelper as flaskhelper
import src.backend as backend


def load_urls():
    flaskhelper.register(backend.init)


app = flaskhelper.app

if __name__ == '__main__':
    load_urls()
    flaskhelper.app.run()
