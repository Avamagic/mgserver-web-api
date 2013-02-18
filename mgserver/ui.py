from mgserver import app, provider
from flask import render_template, g, redirect
from models import Client, Device
from bson.objectid import ObjectId
from flask.ext.login import login_required
from flask.ext.wtf import Form, TextField, validators

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%d-%m %H:%M'):
    return value.strftime(format)

@app.route('/')
def index():
    if g.user:
        return redirect('devices')
    else:
        return render_template('index.html')

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/devices')
@login_required
def devices():
    devices = Device.find({
        "_id": {"$in": [ObjectId(oid) for oid in g.user.client_ids]},
    })
    return render_template('devices.html', devices=devices)

class CreateClientException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return repr("{} already exist".format(self.name))

class ClientForm(Form):
    name = TextField('Name', [validators.Required()])
    description = TextField('Description')
    callback = TextField('Callback',
                         [validators.Required(),
                          validators.URL(require_tld=False)])

def create_client(name, description, callback):
    client = Client.find_one({"resource_owner_id": g.user["_id"], "name": name})
    if client:
        raise CreateClientException(name)

    Client.ensure_index([("resource_owner_id", 1), ("created_at", -1)])
    Client.ensure_index([("resource_owner_id", 1), ("name", 1)])
    Client.ensure_index("client_key")

    client_dict = {
        u"name": name,
        u"description": description,
        u"client_key": provider.generate_client_key(),
        u"secret": provider.generate_client_secret(),
        u"resource_owner_id": g.user["_id"],
        u"callbacks": [callback,],
    }
    client = Client(**client_dict)
    client_id = Client.insert(client)

@app.route('/apps', methods=['GET', 'POST'])
@login_required
def apps():
    form = ClientForm()
    if form.validate_on_submit():
        try:
            create_client(form.name.data,
                          form.description.data,
                          form.callback.data)
        except CreateClientException as e:
            flash("{}".format(e))
        return redirect('apps')

    clients = Client.find({"resource_owner_id": g.user["_id"]}).sort("created_at", -1)
    return render_template('apps.html', clients=clients, form=form)
