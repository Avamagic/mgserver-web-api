from mgserver import app
from flask import flash, render_template, g, session, request, redirect, url_for
from models import ResourceOwner as User
from bson.objectid import ObjectId
from flask.ext.bcrypt import Bcrypt
from utils import RedirectForm
from flask.ext.wtf import TextField, PasswordField, BooleanField, validators
from flask.ext.login import LoginManager, current_user, login_required, login_user, logout_user

bcrypt = Bcrypt(app)
manager = LoginManager()
manager.setup_app(app)
manager.login_view = 'login'


@manager.user_loader
def load_user(userid):
    user_dict = User.find_one({'_id': ObjectId(userid)})
    if user_dict:
        user = User()
        user.update(user_dict)
        return user
    else:
        return None


def get_valid_user(email, pw = ""):
    """Return instance of models.ResourceOwner if credentials are valid
    """
    pw_hash = bcrypt.generate_password_hash(app.config['DUMMY_PASSWORD'])
    user_dict = User.find_one({'email': email})
    if user_dict and 'pw_hash' in user_dict:
        pw_hash = user_dict['pw_hash']

    if bcrypt.check_password_hash(pw_hash, pw) and user_dict:
        user = User()
        user.update(user_dict)
        return user
    else:
        return None


@app.before_request
def before_request():
    if not current_user.is_anonymous():
        g.user = current_user
    else:
        g.user = None


class LoginForm(RedirectForm):
    email = TextField('Email address', [validators.Email()])
    password = PasswordField('Password', [validators.Required()])
    remember = BooleanField('Remember me')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # if we are already logged in
    if g.user:
        return redirect(url_for('index'))

    form = LoginForm()
    error = None
    if form.validate_on_submit():
        user = get_valid_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=form.remember.data)
            flash('Signed in successfully.')
            return form.redirect('index')
        else:
            error = "Invalid credentials"

    return render_template('login.html', form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'You have been signed out')
    return redirect(url_for('index'))


class SignupException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SignupForm(RedirectForm):
    name = TextField('Name', [validators.Required()])
    email = TextField('Email address', [validators.Email()])
    password = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat password')


def create_user(email, passwd="", name=""):
    user = User.find_one({'email': email})
    if user:
        raise SignupException('This email address is already signed up')

    user_dict = {
        u"email": email,
        u"pw_hash": bcrypt.generate_password_hash(passwd),
        u"name": name,
    }
    user = User(**user_dict)
    user_id = User.insert(user)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # if we are already logged in
    if g.user:
        return redirect(url_for('index'))

    form = SignupForm()
    error = None
    if form.validate_on_submit():
        try:
            create_user(form.email.data, form.password.data, form.name.data)
            return form.redirect('index')
        except SignupException as e:
            error = e.value

    return render_template('signup.html', error=error, form=form)
