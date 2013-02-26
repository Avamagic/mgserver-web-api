from flask import Blueprint, render_template, redirect, flash, url_for
from flask.ext.login import current_user, login_required, login_user, logout_user
from bson.objectid import ObjectId
from ..common import CreateClientException, SignupException
from ..database import Client, Device
from ..database import create_user, create_client
from .forms import LoginForm, SignupForm, ClientForm
from .utils import get_valid_user


frontend = Blueprint('frontend', __name__)


@frontend.route('/')
def index():
    if current_user.is_authenticated():
        return redirect(url_for('frontend.devices'))
    else:
        return render_template('index.html')


@frontend.route('/account')
@login_required
def account():
    return render_template('account.html')


@frontend.route('/devices')
@login_required
def devices():
    devices = Device.find({
        "_id": {"$in": [ObjectId(oid) for oid in current_user.client_ids]},
    })
    return render_template('devices.html', devices=devices)


@frontend.route('/apps', methods=['GET', 'POST'])
@login_required
def apps():
    form = ClientForm()
    if form.validate_on_submit():
        try:
            create_client(current_user._get_current_object(),
                          form.name.data,
                          form.description.data,
                          form.callback.data)
        except CreateClientException as e:
            flash("{}".format(e))
        return redirect(url_for('frontend.apps'))

    clients = Client.find({"resource_owner_id": current_user["_id"]}).sort("created_at", -1)
    return render_template('apps.html', clients=clients, form=form)


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    # if we are already logged in
    if current_user.is_authenticated():
        return redirect(url_for('frontend.index'))

    form = LoginForm()
    error = None
    if form.validate_on_submit():
        user = get_valid_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=form.remember.data)
            flash('Signed in successfully.')
            return form.redirect('frontend.index')
        else:
            error = "Invalid credentials"

    return render_template('login.html', form=form, error=error)


@frontend.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'You have been signed out.')
    return redirect(url_for('frontend.index'))


@frontend.route('/signup', methods=['GET', 'POST'])
def signup():
    # if we are already logged in
    if current_user.is_authenticated():
        return redirect(url_for('frontend.index'))

    form = SignupForm()
    error = None
    if form.validate_on_submit():
        try:
            user = create_user(form.email.data, form.password.data, form.name.data)
            login_user(user)
            flash("Created account successfully.")
            return form.redirect('frontend.index')
        except SignupException as e:
            error = e.value

    return render_template('signup.html', error=error, form=form)
