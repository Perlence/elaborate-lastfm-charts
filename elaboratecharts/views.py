from __future__ import division

from collections import OrderedDict, defaultdict
from itertools import islice

import arrow
import mongokit
from flask import Blueprint, jsonify, request, render_template, g
from gevent import spawn
from gevent.pool import Pool
from lastfmclient import LastfmClient
from lastfmclient.exceptions import LastfmError

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

    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)

    try:
        registered = get_registered(dbuser, api)
    except LastfmError as exc:
        response = jsonify(errors=[exc.message])
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

    pool = Pool(config.POOL_SIZE)
    greenlets = [(s, pool.spawn(get_weekly_artist_charts, dbuser, api, s, e))
                 for s, e in span_range]
    pool.join()

    results = OrderedDict()
    errors = []
    for from_date, greenlet in greenlets:
        try:
            charts = greenlet.get()
        except LastfmError as exc:
            errors.append('Failed to get charts for %s: %s' %
                          (from_date.isoformat(), exc.message))
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

    spawn(dbuser.save)
    results['errors'] = errors
    return jsonify(results)


def get_registered(dbuser, api):
    registered = dbuser.get('registered')
    if registered is None:
        registered = api.user.get_info(dbuser['_id'])['registered']['unixtime']
        dbuser['registered'] = arrow.get(registered)
    return registered


def get_weekly_artist_charts(dbuser, api, from_date, to_date):
    week_start = arrow.get().floor('week')
    is_current_week = week_start.replace(hours=-12) == from_date

    weekly_artist_charts = dbuser.setdefault('weekly_artist_charts', [])

    if not is_current_week:
        # Naive search
        for charts in weekly_artist_charts:
            if charts['from'] == from_date:
                return charts['artists']
        charts = api.user.get_weekly_artist_chart(dbuser['_id'],
                                                  from_=from_date.timestamp,
                                                  to=to_date.timestamp)
    else:
        charts = api.user.get_weekly_artist_chart(dbuser['_id'])

    charts_artist = charts.get('artist')
    if charts_artist is None:
        return []
    elif isinstance(charts_artist, list):
        result = [{'artist': artist['name'],
                   'count': int(artist['playcount'])}
                  for artist in charts_artist]
    else:
        artist = charts_artist
        result = [{'artist': artist['name'],
                   'count': int(artist['playcount'])}]

    if not is_current_week:
        dbuser['weekly_artist_charts'].append({
            'from': from_date,
            'to': to_date,
            'artists': result,
        })
    return result
