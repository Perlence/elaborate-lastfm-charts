from gevent import iwait
from gevent.pool import Pool
from gevent import monkey
monkey.patch_all(select=False, thread=False)

import arrow
import yaml
from flask import Blueprint, Response, request, render_template
from pylast import LastFMNetwork

from . import config

app = Blueprint('elaboratecharts', __name__)


def yamlify(obj, *args, **kwargs):
    return Response(yaml.dump(obj),
                    mimetype='application/x-yaml',
                    *args, **kwargs)


def get_weekly_artist_charts(user, from_date, to_date):
    from_date = from_date.replace(hours=-12).timestamp
    to_date = to_date.replace(hours=-12, microseconds=+1).timestamp
    result = user.get_weekly_artist_charts(from_date, to_date)
    return from_date, result


@app.route('/weekly-artist-charts')
def weekly():
    username = request.args.get('username')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    if username is None:
        return yamlify({'error': 'missing username'}, status=400)

    api = LastFMNetwork(config.API_KEY, config.SECRET_KEY)
    try:
        user = api.get_user(username)
    except:
        return yamlify({'error': 'failed to get user'}, status=503)

    if from_date is None:
        from_date = user.get_registered()

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)
    span_range = arrow.Arrow.span_range('week', from_date, to_date)

    pool = Pool(36)
    greenlets = [pool.spawn(get_weekly_artist_charts, user, s, e)
                 for s, e in span_range]

    def generate():
        yield '---\n'
        for greenlet in iwait(greenlets):
            from_date, week = greenlet.get()
            items = [[topitem.item.network, topitem.weight]
                     for topitem in week]
            result = {from_date: items}
            yield yaml.dump(result, Dumper=yaml.dumper.SafeDumper)

    return Response(generate(), mimetype='application/x-yaml')

@app.route('/')
def index():
    return render_template('index.html')
