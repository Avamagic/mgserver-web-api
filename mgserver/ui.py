from mgserver import app
from flask import render_template, g, redirect
from models import Client
from bson.objectid import ObjectId
from flask.ext.login import login_required

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%d-%m %H:%M'):
    return value.strftime(format)

@app.route('/')
def index():
    if g.user:
        return redirect('cameras')
    else:
        return render_template('index.html')

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/cameras')
@login_required
def cameras():
    clients = Client.get_collection().find(
        {'_id': {'$in': [ObjectId(oid) for oid in g.user.client_ids]}}
    ) if (g.user is not None) else None
    return render_template('cameras.html', clients=clients)
