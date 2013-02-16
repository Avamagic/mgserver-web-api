from mgserver import app, provider
from flask import render_template, g, redirect
from models import Client, App
from bson.objectid import ObjectId
from flask.ext.login import login_required
from flask.ext.wtf import Form, TextField, validators

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

class AppForm(Form):
    name = TextField('Name', [validators.Required()])
    description = TextField('Description')

def create_app(name, description):
    app_dict = {
        u"name": name,
        u"description": description,
        u"client_key": provider.generate_client_key(),
        u"secret": provider.generate_client_secret(),
        u"resource_owner_id": g.user["_id"],
    }
    app = App(**app_dict)
    App.ensure_index([("resource_owner_id", 1), ("created_at", -1)])
    app_id = App.insert(app)

@app.route('/apps', methods=['GET', 'POST'])
@login_required
def apps():
    form = AppForm()
    if form.validate_on_submit():
        create_app(form.name.data, form.description.data)
        redirect('apps')

    apps = App.find({"resource_owner_id": g.user["_id"]}).sort("created_at", -1)
    return render_template('apps.html', apps=apps, form=form)
