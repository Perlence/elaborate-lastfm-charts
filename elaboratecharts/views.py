from gevent.pool import Pool
from gevent import monkey
monkey.patch_all(select=False, thread=False)

import arrow
from flask import Blueprint, render_template, jsonify
from pylast import LastFMNetwork

from . import config

app = Blueprint('elaboratecharts', __name__)


@app.route(
    '/weekly-artist-charts/<username>',
    defaults={'from_date': None, 'to_date': None})
@app.route(
    '/weekly-artist-charts/<username>/<from_date>',
    defaults={'to_date': None})
@app.route(
    '/weekly-artist-charts/<username>/<from_date>/<to_date>')
def weekly(username, from_date, to_date):
    api = LastFMNetwork(config.API_KEY, config.SECRET_KEY)
    user = api.get_user(username)

    if from_date is None:
        from_date = user.get_registered()

    from_date = arrow.get(from_date).floor('week')
    to_date = arrow.get(to_date).ceil('week')

    pool = Pool(64)
    span_range = arrow.Arrow.span_range('week', from_date, to_date)
    greenlets = [pool.spawn(user.get_weekly_artist_charts,
                            s.replace(hours=-12).timestamp,
                            e.replace(hours=-12, microseconds=+1).timestamp)
                 for s, e in span_range]
    pool.join()
    results = [greenlet.get() for greenlet in greenlets]
    return jsonify(results=[{topitem.item.network: topitem.weight
                             for topitem in week}
                            for week in results])
