# -*- encoding: utf-8 -*-
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
RETRIES = 3
TIMEOUT = 5


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

redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT,
              db=config.REDIS_DB, password=config.REDIS_PASSWORD)
app = elaboratecharts = Blueprint('elaboratecharts', __name__,
                                  template_folder='templates',
                                  static_folder='static')


@app.route('/')
def index():
    context = {
        'chart_types': [
            ('artist', 'Artists'),
            ('album', 'Albums'),
            ('track', 'Tracks'),
        ],
        'numbers_of_positions': [
            (5, 5),
            (10, 10),
            (15, 15),
            (20, 20),
            (30, 30),
            (50, 50),
        ],
        'timeframes': [
            ('last-7-days', 'Last 7 days'),
            ('last-month', 'Last month'),
            ('last-3-months', 'Last 3 months'),
            ('last-6-months', 'Last 6 months'),
            ('last-12-months', 'Last 12 months'),
            ('overall', 'Overall'),
        ],
    }
    return render_template('index.html', **context)


@app.route('/weekly-chart')
def weekly_chart():
    username = request.args.get('username').lower()
    chart_type = request.args.get('chartType').lower()
    from_date = request.args.get('fromDate')
    to_date = request.args.get('toDate')

    if chart_type not in ('artist', 'album', 'track'):
        response = jsonify(error='Unknown chart type: %s' % chart_type)
        response.status_code(400)
        return response

    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)
    dbuser = User(redis, username)

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)

    for __ in range(RETRIES):  # try several times
        timeout = Timeout(TIMEOUT)
        timeout.start()
        result = {'toDate': to_date.timestamp}
        try:
            chart = get_weekly_chart(api, dbuser, chart_type,
                                     from_date, to_date)
        except LastfmError as exc:
            result['error'] = 'Failed to get chart for %s: %s' % (
                to_date.isoformat(), exc.message)
        except Timeout as t:
            if t is not timeout:
                raise
            result['error'] = 'Failed to get chart for %s: %s' % (
                to_date.isoformat(), 'timed out')
        else:
            result['chart'] = chart
            result.pop('error', None)
            break
        finally:
            timeout.cancel()

    return jsonify(result)


@app.route('/info')
def get_registered():
    username = request.args.get('username')

    dbuser = User(redis, username)
    api = LastfmClient(api_key=config.API_KEY, api_secret=config.API_SECRET)

    registered = dbuser.get_registered()
    if registered is None:
        try:
            registered = arrow.get(
                pool.spawn(api.user.get_info, username)
                    .get()['registered']['unixtime'])
        except LastfmError as err:
            response = jsonify(error=err.message)
            response.status_code = 502
            return response
        spawn(dbuser.set_registered, registered)

    return jsonify(registered=registered.timestamp)


def get_weekly_chart(api, dbuser, chart_type, from_date, to_date):
    week_start = arrow.get().floor('week')
    is_current_week = week_start.replace(hours=-12) == from_date

    get_weekly_smth_chart = getattr(api.user,
                                    'get_weekly_%s_chart' % chart_type)

    if not is_current_week:
        cached_chart = dbuser.get_weekly_chart(chart_type,
                                               from_date, to_date)
        if cached_chart is not None:
            return cached_chart

        response = pool.spawn(get_weekly_smth_chart,
                              dbuser.username,
                              from_=from_date.timestamp,
                              to=to_date.timestamp).get()
    else:
        response = pool.spawn(get_weekly_smth_chart,
                              dbuser.username).get()

    if response == 'ok':
        raise LastfmError('invalid response')

    chart = response.get(chart_type)
    if chart is None:
        result = {}
    elif isinstance(chart, list):
        result = {chart_key(chart_type, item): int(item['playcount'])
                  for item in chart}
    else:
        item = chart
        result = {chart_key(chart_type, item): int(item['playcount'])}

    if not is_current_week:
        spawn(dbuser.set_weekly_chart, chart_type, from_date, to_date, result)

    return result


def chart_key(chart_type, item):
    if chart_type == 'artist':
        return item['name']
    elif chart_type in ('album', 'track'):
        return item['artist']['#text'] + u' – ' + item['name']
