from __future__ import division

from collections import OrderedDict, defaultdict
from functools import partial
from itertools import islice, izip

import arrow
import mongokit
from flask import Blueprint, jsonify, request, render_template, g
from gevent import spawn, sleep, joinall, wait
from gevent.pool import Pool
from gevent.lock import RLock
from lastfmclient import LastfmClient
from lastfmclient.exceptions import LastfmError

from . import config
from .models import documents


POOL_SIZE = 52
LASTFM_PAGE_SIZE = 200
LASTFM_INTERVAL = 0.25


class ThrottlingPool(Pool):
    def __init__(self, size=None, interval=None, greenlet_class=None):
        self.interval = interval
        self._lock = RLock()
        super(ThrottlingPool, self).__init__(size, greenlet_class)

    def wait_available(self):
        wait(self._lock, self._semaphore)

    def add(self, greenlet):
        self._lock.acquire()
        try:
            super(ThrottlingPool, self).add(greenlet)
        except:
            self._lock.release()
            raise
        else:
            sleep(self.interval)
            self._lock.release()

pool = ThrottlingPool(POOL_SIZE, LASTFM_INTERVAL)

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

    greenlets = [spawn(get_weekly_artist_charts, dbuser, api, s, e)
                 for s, e in span_range]
    joinall(greenlets)

    results = OrderedDict()
    errors = []
    for (s, __), greenlet in izip(span_range, greenlets):
        try:
            charts = greenlet.get()
        except LastfmError as exc:
            errors.append('Failed to get charts for %s: %s' %
                          (s.isoformat(), exc.message))
        else:
            results[s.timestamp] = charts

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
                return OrderedDict((chart['artist'], chart['count'])
                                   for chart in charts['artists'])

    get_page = partial(pool.spawn, get_recent_tracks, dbuser, api,
                       from_date, to_date)
    greenlets = [get_page(page=1)]
    total_pages, tracks = greenlets[0].get()
    for page in range(2, total_pages + 1):
        greenlet = get_page(page=page)
        greenlets.append(greenlet)
        sleep(LASTFM_INTERVAL)
    joinall(greenlets)

    charts = defaultdict(int)
    for greenlet in greenlets:
        __, tracks = greenlet.get()
        for track in tracks:
            charts[track['artist']] += 1

    result = OrderedDict(sorted(charts.iteritems(),
                                key=lambda (__, v): v,
                                reverse=True))

    if not is_current_week:
        dbuser['weekly_artist_charts'].append({
            'from': from_date,
            'to': to_date,
            'artists': [{'artist': artist, 'count': count}
                        for artist, count in result.iteritems()],
        })
    return result


def get_recent_tracks(dbuser, api, from_date, to_date, page):
    response = api.user.get_recent_tracks(
        dbuser['_id'], from_=from_date.timestamp, to=to_date.timestamp,
        limit=LASTFM_PAGE_SIZE, page=page)
    total_pages = int(response['@attr']['totalPages'])
    recent_tracks = response.get('track')
    flatten = lambda track: {
        'artist': track['artist']['#text'],
        'album': track['album']['#text'],
        'name': track['name'],
    }
    if recent_tracks is None:
        return 0, []
    elif isinstance(recent_tracks, list):
        result = list(map(flatten, recent_tracks))
    else:
        track = recent_tracks
        result = [flatten(track)]
    return total_pages, result
