import arrow


class User(object):
    """Cached weekly charts for user.

    Cache is structured as following::

    -   *hash* Registered:
        ``{collection}:{username}:info``
    -   *hash* Weekly artist charts:
        ``{collection}:{username}:weekly_artist_charts:{from}-{to}``
    -   *hash* Weekly album charts:
        ``{collection}:{username}:weekly_album_charts:{from}-{to}``
    -   *hash* Weekly track charts:
        ``{collection}:{username}:weekly_track_charts:{from}-{to}``
    """

    collection = 'elaboratecharts'

    def __init__(self, redis, username, collection=None):
        self.redis = redis
        self.username = username
        self.collection = collection or User.collection

    @property
    def prefix(self):
        return '{collection}:{username}'.format(**vars(self))

    def with_prefix(self, operation, key, *args, **kwargs):
        method = getattr(self.redis, operation)
        return method(self.prefix + ':' + key, *args, **kwargs)

    def get_registered(self):
        registered = self.with_prefix('hget', 'info', 'registered')
        if registered is not None:
            return arrow.get(registered)

    def set_registered(self, registered):
        self.with_prefix('hset', 'info', 'registered', registered.timestamp)

    def get_weekly_chart(self, chart_type, from_date, to_date):
        charts = self.with_prefix(
            'hgetall',
            'weekly_{chart_type}_chart:{from_date}_{to_date}'.format(
                chart_type=chart_type,
                from_date=from_date.timestamp,
                to_date=to_date.timestamp))
        if charts == {}:
            return None
        elif charts == {'__EMPTY__': '-1'}:
            return {}
        else:
            return dict(zip(charts.iterkeys(), map(int, charts.itervalues())))

    def set_weekly_chart(self, chart_type, from_date, to_date, charts):
        if not charts:
            charts = {'__EMPTY__': '-1'}
        for artist, count in charts.iteritems():
            self.with_prefix(
                'hset',
                'weekly_{chart_type}_chart:{from_date}_{to_date}'.format(
                    chart_type=chart_type,
                    from_date=from_date.timestamp,
                    to_date=to_date.timestamp),
                artist,
                count)

    def get_weekly_artist_charts(self, from_date, to_date):
        return self.get_weekly_chart('weekly_artist_charts',
                                     from_date, to_date)

    def get_weekly_album_charts(self, from_date, to_date):
        return self.get_weekly_chart('weekly_album_charts',
                                     from_date, to_date)

    def get_weekly_track_charts(self, from_date, to_date):
        return self.get_weekly_chart('weekly_track_charts',
                                     from_date, to_date)

    def set_weekly_artist_charts(self, from_date, to_date, charts):
        self.set_weekly_chart('weekly_artist_charts',
                              from_date, to_date, charts)

    def set_weekly_album_charts(self, from_date, to_date, charts):
        self.set_weekly_chart('weekly_album_charts',
                              from_date, to_date, charts)

    def set_weekly_track_charts(self, from_date, to_date, charts):
        self.set_weekly_chart('weekly_track_charts',
                              from_date, to_date, charts)
