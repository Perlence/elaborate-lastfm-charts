from __future__ import division

from collections import OrderedDict

import arrow
import mongokit
from flask import Blueprint, jsonify, request, render_template, g
from gevent import Timeout, spawn, sleep, wait
from gevent.pool import Pool
from gevent.lock import RLock
from lastfmclient import LastfmClient
from lastfmclient.exceptions import LastfmError

from . import config
from .models import documents


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
    username = request.args.get('username').lower()
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')

    dbuser = (g.db.User.find_one({'_id': username}) or
              g.db.User({'_id': username}))

    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)

    timeout = Timeout(TIMEOUT)
    timeout.start()
    results = OrderedDict()
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

    dbuser = (g.db.User.find_one({'_id': username}) or
              g.db.User({'_id': username}))

    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)

    registered = dbuser.get('registered')
    if registered is None:
        registered = arrow.get(
            api.user.get_info(username)['registered']['unixtime'])
        dbuser['registered'] = registered
        spawn(g.db.User.find_and_modify,
              {'_id': dbuser['_id']},
              {'$set': {'registered': registered.datetime}},
              upsert=True)

    return jsonify(registered=registered.timestamp)


def get_weekly_artist_charts(dbuser, api, from_date, to_date):
    week_start = arrow.get().floor('week')
    is_current_week = week_start.replace(hours=-12) == from_date

    weekly_artist_charts = dbuser.setdefault('weekly_artist_charts', [])

    if not is_current_week:
        # Naive search
        for charts in weekly_artist_charts:
            if charts['from'] == from_date and charts['to'] == to_date:
                return OrderedDict((chart['artist'], chart['count'])
                                   for chart in charts['artists'])
        charts = api.user.get_weekly_artist_chart(dbuser['_id'],
                                                  from_=from_date.timestamp,
                                                  to=to_date.timestamp)
    else:
        charts = api.user.get_weekly_artist_chart(dbuser['_id'])

    charts_artist = charts.get('artist')
    if charts_artist is None:
        return OrderedDict()
    elif isinstance(charts_artist, list):
        result = OrderedDict((artist['name'], int(artist['playcount']))
                             for artist in charts_artist)
    else:
        artist = charts_artist
        result = OrderedDict([(artist['name'], int(artist['playcount']))])

    if not is_current_week:
        doc = {
            'from': from_date.datetime,
            'to': to_date.datetime,
            'artists': [{'artist': artist_, 'count': count}
                        for artist_, count in result.iteritems()],
        }
        spawn(g.db.User.find_and_modify,
              {'_id': dbuser['_id']},
              {'$push': {'weekly_artist_charts': doc}})
    return result
