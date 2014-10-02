from gevent import monkey
monkey.patch_all(select=False, thread=False)

from functools import partial

from flask import Flask

from . import config
from .views import app as elaboratecharts

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

app.register_blueprint(elaboratecharts)


def start(debug=False):
    import os
    if debug or 'DEBUG' in os.environ:
        host = '127.0.0.1'
        debug = True
    else:
        host = '0.0.0.0'
    app.debug = debug
    app.run(host=host, port=5000)

debug = partial(start, debug=True)
