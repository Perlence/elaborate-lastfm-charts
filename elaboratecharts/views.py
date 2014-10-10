from __future__ import division

from collections import OrderedDict, defaultdict
from itertools import islice

import arrow
import mongokit
from flask import Blueprint, jsonify, request, render_template, g
from gevent import spawn
from gevent.pool import Pool
from pylast import LastFMNetwork, WSError

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
    number_of_artists = request.args.get('numberOfArtists', type=int)
    timeframe = request.args.get('timeframe')
    cumulative = request.args.get('cumulative', type=lambda x: x == 'true')

    dbuser = (g.db.User.find_one({'_id': username}) or
              g.db.User({'_id': username}))

    api = LastFMNetwork(config.API_KEY, config.API_SECRET)
    user = api.get_user(username)

    try:
        registered = get_registered(dbuser, user)
    except WSError as err:
        response = jsonify(errors=[err.details])
        response.status_code = 500
        return response

    to_date = arrow.get()
    if timeframe == 'last-7-days':
        from_date = to_date.replace(weeks=-1)
    elif timeframe == 'last-month':
        from_date = to_date.replace(months=-1)
    elif timeframe == 'last-3-months':
        from_date = to_date.replace(months=-3)
    elif timeframe == 'last-6-months':
        from_date = to_date.replace(months=-6)
    elif timeframe == 'last-12-months':
        from_date = to_date.replace(months=-12)
    elif timeframe == 'overall':
        from_date = arrow.get(registered)
    else:
        response = jsonify(errors=['Unrecognized timeframe'])
        response.status_code = 400
        return response

    span_range = arrow.Arrow.span_range('week', from_date, to_date)
    span_range = [(s.replace(hours=-12),
                   e.replace(hours=-12, microseconds=+1))
                  for s, e in span_range]

    pool = Pool(72)
    greenlets = [(s, pool.spawn(get_weekly_artist_charts, dbuser, user, s, e))
                 for s, e in span_range]
    pool.join()

    results = OrderedDict()
    errors = []
    for from_date, greenlet in greenlets:
        try:
            charts = greenlet.get()
        except WSError as err:
            errors.append('Failed to get charts for %s: %s' %
                          (from_date.isoformat(), err.details))
        else:
            items = OrderedDict((item['artist'], item['count'])
                                for item in charts)
            results[from_date.timestamp] = items

    if cumulative:
        artists_acc = defaultdict(int)
        for timestamp, charts in results.iteritems():
            for artist, count in charts.iteritems():
                artists_acc[artist] += charts[artist]
                charts[artist] = artists_acc[artist]
            for artist, count in artists_acc.iteritems():
                if artist not in charts:
                    charts[artist] = count

    # Limit the number of artists
    for timestamp, charts in results.iteritems():
        charts = sorted(charts.iteritems(),
                        key=lambda (__, count): count,
                        reverse=True)
        results[timestamp] = OrderedDict(islice(charts, 0, number_of_artists))

    # Would be better to save document after response is sent.
    dbuser.save()
    results['errors'] = errors
    return jsonify(results)


def get_registered(dbuser, user):
    registered = dbuser.get('registered')
    if registered is None:
        registered = user.get_registered()
        dbuser['registered'] = arrow.get(registered)
    return registered


def get_weekly_artist_charts(dbuser, user, from_date, to_date):
    week_start = arrow.get().floor('week')
    is_current_week = week_start.replace(hours=-12) == from_date

    weekly_artist_charts = dbuser.setdefault('weekly_artist_charts', [])

    if not is_current_week:
        # Naive search
        for charts in weekly_artist_charts:
            if charts['from'] == from_date:
                return charts['artists']
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
    return result
