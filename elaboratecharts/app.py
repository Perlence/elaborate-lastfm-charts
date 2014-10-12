from gevent.wsgi import WSGIServer
from gevent import monkey
monkey.patch_all(select=False, thread=False)

from functools import partial
from os import path

from flask import Flask
from flask.ext.assets import Environment, Bundle
from werkzeug.serving import run_with_reloader

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
    'ladda-bootstrap/dist/spin.min.js',
    'ladda-bootstrap/dist/ladda.min.js',
    Bundle(
        'index.coffee',
        filters=['coffeescript']),
    output='js_all.js')
css_bundle = Bundle(
    'all.scss',
    filters=['scss'],
    output='css_all.css')
env.config['sass_load_paths'] = [
    path.join(path.dirname(__file__), 'bower_components/bootstrap-sass/lib/'),
    path.join(path.dirname(__file__), 'bower_components/ladda-bootstrap/css/')
]
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
    http_server = WSGIServer((host, 5000), app)
    http_server.serve_forever()


def debug():
    run_with_reloader(partial(start, debug=True))
