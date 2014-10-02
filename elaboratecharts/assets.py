import logging
from os import path

from webassets import Environment, Bundle
from webassets.script import CommandLineEnvironment

env = Environment(path.join(path.dirname(__file__), 'static'), '/static')
# env.manifest = ''
# env.cache = False

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


def cli():
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)
    return CommandLineEnvironment(env, log)


def build():
    cli().build()


def watch():
    cli().watch()


def clean():
    cli().watch()
