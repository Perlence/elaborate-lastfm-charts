from flask import Flask

from . import config
from . import ElaborateCharts


app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
charts = ElaborateCharts(app)


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
