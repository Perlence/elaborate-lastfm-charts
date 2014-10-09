import json
from collections import OrderedDict

import arrow
import mongokit
from flask import Blueprint, request, render_template, g
from gevent import spawn
from gevent.pool import Pool
from pylast import LastFMNetwork

from . import config
from .models import documents

app = Blueprint('elaboratecharts', __name__)


@app.before_request
def connect_to_mongodb():
    g.db = mongokit.Connection(config.MONGODB_HOST, use_greenlets=True)
    g.db.register(documents)


@app.after_request
def disconnect_from_mongodb(response):
    g.db.disconnect()
    return response


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weekly-artist-charts')
def weekly_artist_charts():
    username = request.args.get('username')
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')
    cumulative = request.args.get('cumulative', type=bool)

    dbuser = (g.db.User.find_one({'_id': username}) or
              g.db.User({'_id': username}))

    api = LastFMNetwork(config.API_KEY, config.API_SECRET)
    user = api.get_user(username)

    if from_date is None:
        from_date = get_registered(dbuser, user)

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)
    span_range = arrow.Arrow.span_range('week', from_date, to_date)

    pool = Pool(72)
    greenlets = [pool.spawn(get_weekly_artist_charts, dbuser, user, s, e)
                 for s, e in span_range]
    pool.join()

    results = OrderedDict()
    for greenlet in greenlets:
        from_date, charts = greenlet.get()
        items = OrderedDict((item['artist'], item['count'])
                            for item in charts)
        results[from_date.timestamp] = items

    # Would be better to save document after response is sent.
    dbuser.save()
    return json.dumps(results)


def get_registered(dbuser, user):
    registered = dbuser.get('registered')
    if registered is None:
        registered = user.get_registered()
        dbuser['registered'] = arrow.get(registered)
    return registered


def get_weekly_artist_charts(dbuser, user, from_date, to_date):
    is_current_week = arrow.get().floor('week') == from_date
    from_date = from_date.replace(hours=-12)
    to_date = to_date.replace(hours=-12, microseconds=+1)

    weekly_artist_charts = dbuser.setdefault('weekly_artist_charts', [])

    if not is_current_week:
        # Naive search
        for charts in weekly_artist_charts:
            if charts['from'] == from_date:
                return from_date, charts['artists']
        charts = user.get_weekly_artist_charts(from_date.timestamp,
                                               to_date.timestamp)
    else:
        charts = user.get_weekly_artist_charts()

    result = [{'artist': topitem.item.network, 'count': topitem.weight}
              for topitem in charts]
    if not is_current_week:
        dbuser['weekly_artist_charts'].append({
            'from': from_date,
            'to': to_date,
            'artists': result,
        })
    return from_date, result
