import json
from collections import OrderedDict

import arrow
from flask import Blueprint, request, render_template
from gevent import iwait
from gevent.pool import Pool
from pylast import LastFMNetwork

from . import config

app = Blueprint('elaboratecharts', __name__)


@app.route('/')
def index():
    return render_template('index.html')


def get_weekly_artist_charts(user, from_date, to_date):
    from_date = from_date.replace(hours=-12).timestamp
    to_date = to_date.replace(hours=-12, microseconds=+1).timestamp
    result = user.get_weekly_artist_charts(from_date, to_date)
    return from_date, result


@app.route('/weekly-artist-charts')
def weekly_artist_charts():
    username = request.args.get('username')
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')

    api = LastFMNetwork(config.API_KEY, config.API_SECRET)
    user = api.get_user(username)

    if from_date is None:
        from_date = user.get_registered()

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)
    span_range = arrow.Arrow.span_range('week', from_date, to_date)

    pool = Pool(72)
    greenlets = [pool.spawn(get_weekly_artist_charts, user, s, e)
                 for s, e in span_range]
    pool.join()

    results = OrderedDict()
    for greenlet in greenlets:
        from_date, week = greenlet.get()
        items = OrderedDict((topitem.item.network, topitem.weight)
                            for topitem in week)
        results[from_date] = items
    return json.dumps(results)
