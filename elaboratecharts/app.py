from functools import partial

import flask

app = flask.Flask(__name__)


def start(debug=False):
    import os
    if debug or 'DEBUG' in os.environ:
        host = '127.0.0.1'
        debug = True
    else:
        host = '0.0.0.0'
    app.run(host=host, port=5000, debug=debug)

debug = partial(start, debug=True)
