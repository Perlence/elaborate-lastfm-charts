from gevent.wsgi import WSGIServer
from gevent import monkey
monkey.patch_all(select=False, thread=False)

from functools import partial

from flask import Flask
from werkzeug.serving import run_with_reloader

from . import config
from . import ElaborateCharts


app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
charts = ElaborateCharts(app)


def start(debug=False):
    host = config.HOST
    if host is None:
        host = '127.0.0.1' if debug else '0.0.0.0'
    app.debug = debug
    http_server = WSGIServer((host, 5000), app)
    http_server.serve_forever()


def debug():
    run_with_reloader(partial(start, debug=True))
