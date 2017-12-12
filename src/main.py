# -*- coding: utf-8 -*-
import server.helper.flaskhelper as flaskhelper
import backend



if __name__ == '__main__':
    flaskhelper.register(backend.urls)
    flaskhelper.app.run()
