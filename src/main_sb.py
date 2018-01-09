# Special imports for special modes
import server.helper.flaskhelper as flaskhelper
import backend as karpbackend
import skbl.skblbackend
import sb.server.backend as sbbackend


def load_urls():
    flaskhelper.register(karpbackend.init())
    flaskhelper.register(skbl.skblbackend.init())
    flaskhelper.register(sbbackend.init())

app = flaskhelper.app

if __name__ == '__main__':
    # when run without the wsgi (in docker)
    load_urls()
    flaskhelper.app.run()
