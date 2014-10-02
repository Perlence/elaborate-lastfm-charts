from gevent import monkey
monkey.patch_all(select=False, thread=False)

from functools import partial
from os import path

from flask import Flask
from flask.ext.assets import Environment, Bundle

from . import config
from .views import app as elaboratecharts

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

env = Environment(app)
env.load_path = [
    path.join(path.dirname(__file__), 'scss'),
    path.join(path.dirname(__file__), 'coffee'),
    path.join(path.dirname(__file__), 'bower_components'),
]
js_bundle = Bundle(
    'jquery/dist/jquery.js',
    'bootstrap-sass/dist/js/bootstrap.js',
    'moment/min/moment-with-locales.js',
    'highcharts-release/highcharts.js',
    Bundle(
        'index.coffee',
        filters=['coffeescript']),
    output='js_all.js')
css_bundle = Bundle(
    'bootstrap-sass/lib/bootstrap.scss',
    'all.scss',
    filters=['pyscss'],
    output='css_all.css')
env.register('js_all', js_bundle)
env.register('css_all', css_bundle)

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
