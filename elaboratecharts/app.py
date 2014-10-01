from functools import partial
from os import path

from flask import Flask, render_template

from . import views

app = Flask(__name__)

app.register_blueprint(views.app)




def start(debug=False):
    import os
    if debug or 'DEBUG' in os.environ:
        host = '127.0.0.1'
        debug = True
    else:
        host = '0.0.0.0'
    app.run(host=host, port=5000, debug=debug)

debug = partial(start, debug=True)
