from gevent import monkey
monkey.patch_all(select=False, thread=False)

from functools import partial
from os import path

from flask import Flask, render_template

from .views import app as elaboratecharts
from .socketio import socketio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

app.register_blueprint(elaboratecharts)
socketio.init_app(app)


def start(debug=False):
    import os
    if debug or 'DEBUG' in os.environ:
        host = '127.0.0.1'
        debug = True
    else:
        host = '0.0.0.0'
    app.debug = debug
    socketio.run(app, host=host, port=5000)

debug = partial(start, debug=True)
