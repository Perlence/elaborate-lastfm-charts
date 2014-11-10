from os import path
from shutil import copytree, rmtree

from flask.ext.assets import Environment, Bundle

from .views import elaboratecharts


def rel(p):
    return path.join(path.dirname(__file__), p)


class ElaborateCharts(object):
    def __init__(self, app=None, url_prefix=None):
        if app is not None:
            self.init_app(app, url_prefix=url_prefix)

    def init_app(self, app, url_prefix=None):
        app.register_blueprint(elaboratecharts, url_prefix=url_prefix)
        self.init_assets(app, url_prefix=url_prefix)

    def init_assets(self, app, url_prefix=None):
        blueprint = app.blueprints['elaboratecharts']
        env = Environment(app)
        env.url = (url_prefix or '') + blueprint.static_url_path
        env.directory = blueprint.static_folder
        env.load_path = map(rel, [
            'scss',
            'coffee',
            'bower_components',
        ])

        js_bundle = Bundle(
            Bundle(
                'jquery/dist/jquery.js',
                'bootstrap-sass-official/assets/javascripts/bootstrap.js',
                'moment/min/moment-with-locales.js',
                'highstock-release/highstock.src.js',
                'ladda-bootstrap/dist/spin.js',
                'ladda-bootstrap/dist/ladda.js',
                'bluebird/js/browser/bluebird.js',
                'lodash/dist/lodash.js',
                ('history.js/scripts/bundled-uncompressed/html4+html5/'
                 'jquery.history.js'),
                'jquery.finger/dist/jquery.finger.js',
                output='js_requirements.js'),
            Bundle(
                'index.coffee',
                filters=['coffeescript'],
                output='js_index.js'))

        css_bundle = Bundle(
            'all.scss',
            filters=['scss'],
            output='css_all.css')
        env.config['sass_load_paths'] = map(rel, [
            'bower_components/bootstrap-sass-official/assets/stylesheets/',
            'bower_components/ladda-bootstrap/css/',
            'bower_components/font-awesome/scss/',
        ])

        # Copy fonts to static folder
        static_fonts = path.join(env.directory, 'fonts')
        try:
            rmtree(static_fonts)
        except OSError:
            pass
        copytree(rel('bower_components/font-awesome/fonts'),
                 static_fonts)

        env.register('js_all', js_bundle)
        env.register('css_all', css_bundle)
