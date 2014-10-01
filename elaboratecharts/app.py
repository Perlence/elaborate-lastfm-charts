from gevent import monkey
monkey.patch_all()

from functools import partial
from os import path

from flask import Flask, render_template
from flask.ext.socketio import SocketIO

from . import views

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

app.register_blueprint(views.app)


@socketio.on('weekly artist charts')
def handle_message(req):
    print req


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
