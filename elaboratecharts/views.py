from flask import Blueprint, render_template

from . import config

app = Blueprint('elaboratecharts', __name__)


@app.route('/')
def index():
    return render_template('index.html')
