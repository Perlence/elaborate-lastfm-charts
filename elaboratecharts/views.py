from __future__ import division

import arrow
from flask import Blueprint, jsonify, request, render_template
from gevent import Timeout, spawn, sleep, wait
from gevent.pool import Pool
from gevent.lock import RLock
from lastfmclient import LastfmClient
from lastfmclient.exceptions import LastfmError
from redis import Redis

from . import config
from .models import User


POOL_SIZE = 52
LASTFM_PAGE_SIZE = 200
LASTFM_INTERVAL = 0.25
TIMEOUT = 20


class ThrottlingPool(Pool):
    def __init__(self, size=None, interval=None, greenlet_class=None):
        self.interval = interval
        self._lock = RLock()
        super(ThrottlingPool, self).__init__(size, greenlet_class)

    def wait_available(self):
        wait(self._lock, self._semaphore)

    def add(self, greenlet):
        self._lock.acquire()
        print 'acquired'
        try:
            super(ThrottlingPool, self).add(greenlet)
        except:
            self._lock.release()
            raise
        else:
            sleep(self.interval)
            self._lock.release()

pool = ThrottlingPool(POOL_SIZE, LASTFM_INTERVAL)

redis = Redis()
app = Blueprint('elaboratecharts', __name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weekly-artist-charts')
def weekly_artist_charts():
    username = request.args.get('username').lower()
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')

    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)
    dbuser = User(redis, username)

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)

    timeout = Timeout(TIMEOUT)
    timeout.start()
    results = {}
    try:
        charts = get_weekly_artist_charts(dbuser, api, from_date, to_date)
    except LastfmError as exc:
        results['error'] = 'Failed to get charts for %s: %s' % (
            to_date.isoformat(), exc.message)
    except Timeout as t:
        if t is not timeout:
            raise
        results['error'] = 'Failed to get charts for %s: %s' % (
            to_date.isoformat(), 'timed out')
    else:
        results[to_date.timestamp] = charts
    finally:
        timeout.cancel()

    return jsonify(results)


@app.route('/info')
def get_registered():
    username = request.args.get('username')

    dbuser = User(redis, username)
    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)

    registered = dbuser.get_registered()
    if registered is None:
        registered = arrow.get(
            pool.spawn(api.user.get_info, username)
                .get()['registered']['unixtime'])
        spawn(dbuser.set_registered, registered)

    return jsonify(registered=registered.timestamp)


def get_weekly_artist_charts(dbuser, api, from_date, to_date):
    week_start = arrow.get().floor('week')
    is_current_week = week_start.replace(hours=-12) == from_date

    if not is_current_week:
        cached_charts = dbuser.get_weekly_artist_charts(from_date, to_date)
        if cached_charts:
            return cached_charts

        charts = pool.spawn(api.user.get_weekly_artist_chart,
                            dbuser.username,
                            from_=from_date.timestamp,
                            to=to_date.timestamp).get()
    else:
        charts = pool.spawn(api.user.get_weekly_artist_chart,
                            dbuser.username).get()

    charts_artist = charts.get('artist')
    if charts_artist is None:
        return {}
    elif isinstance(charts_artist, list):
        result = {artist['name']: int(artist['playcount'])
                  for artist in charts_artist}
    else:
        artist = charts_artist
        result = {artist['name']: int(artist['playcount'])}

    if not is_current_week:
        spawn(dbuser.set_weekly_artist_charts, from_date, to_date, result)

    return result
