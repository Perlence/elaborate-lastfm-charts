from functools import partial
from os import path

from flask import Flask
from flask.ext.assets import Environment, Bundle

from . import views

app = Flask(__name__)

env = Environment(app)

env.load_path = [
    path.join(path.dirname(__file__), 'bower_components'),
]

js_bundle = Bundle(
    'jquery/dist/jquery.min.js',
    'bootstrap-sass/dist/js/bootstrap.min.js',
    output='js_all.js')
css_bundle = Bundle(
    'bootstrap-sass/lib/bootstrap.scss',
    filters=['pyscss'],
    output='css_all.css')

env.register('js_all', js_bundle)
env.register('css_all', css_bundle)

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
