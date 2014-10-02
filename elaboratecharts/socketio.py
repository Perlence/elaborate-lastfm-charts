import arrow
from flask.ext.socketio import SocketIO, emit
from gevent import iwait
from gevent.pool import Pool
from pylast import LastFMNetwork

from . import config

socketio = SocketIO()


def get_weekly_artist_charts(user, from_date, to_date):
    from_date = from_date.replace(hours=-12).timestamp
    to_date = to_date.replace(hours=-12, microseconds=+1).timestamp
    result = user.get_weekly_artist_charts(from_date, to_date)
    return from_date, result


@socketio.on('weekly artist charts')
def weekly_artist_charts(request):
    username = request.get('username')
    from_date = request.get('fromDate')
    to_date = request.get('toDate')

    api = LastFMNetwork(config.API_KEY, config.API_SECRET)
    user = api.get_user(username)

    if from_date is None:
        from_date = user.get_registered()

    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date)
    span_range = arrow.Arrow.span_range('week', from_date, to_date)
    emit('weeks', [s.replace(hours=-12).timestamp for s, _ in span_range])

    pool = Pool(72)
    greenlets = [pool.spawn(get_weekly_artist_charts, user, s, e)
                 for s, e in span_range]

    for greenlet in iwait(greenlets):
        try:
            from_date, week = greenlet.get()
        except Exception as e:
            print e
        items = [[topitem.item.network, topitem.weight]
                 for topitem in week]
        emit('week', [from_date, items])
