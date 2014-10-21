from datetime import datetime

import arrow
import mongokit


class ArrowType(mongokit.CustomType):
    mongo_type = datetime
    python_type = arrow.Arrow

    def to_bson(self, value):
        return value.datetime

    def to_python(self, value):
        if value is not None:
            return arrow.get(value)


class RootDocument(mongokit.Document):
    __database__ = 'elaboratecharts'


class User(RootDocument):
    __collection__ = 'user'
    structure = {
        '_id': unicode,  # Username
        'registered': ArrowType(),
        'weekly_artist_charts': [{
            'from': ArrowType(),
            'to': ArrowType(),
            'artists': [{
                'artist': unicode,
                'count': int,
            }]
        }]
    }

documents = [User]
