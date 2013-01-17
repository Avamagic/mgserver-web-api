from mgserver import app
from flask import flash, render_template, g, session, request
from models import ResourceOwner as User
from bson.objectid import ObjectId
from flask.ext.bcrypt import Bcrypt

bcrypt = Bcrypt(app)

def get_next_url(request):
    """Returns the URL where we want to redirect to.  This will
    always return a valid URL.
    """
    return (
        request.values.get('next') or
        request.referrer or
        request.url_root
    )


def get_valid_user(email, pw):
    """Return instance of models.ResourceOwner if credentials are valid
    """
    user_dict = User.find_one({'email': email}) or User.find_one({'email': app.config['DUMMY_EMAIL']})
    pw_hash = user_dict['pass_hash'] if (user_dict and ('pw_hash' in user_dict)) else app.config['DUMMY_PW_HASH']
    if bcrypt.check_password_hash(pw or "dummy123", pw_hash) and email != app.config['DUMMY_EMAIL']:
        user = User()
        return user.update(user_dict)
    else:
        return None


@app.before_request
def before_request():
    g.user = None
    if 'uid' in session:
        user_dict = User.find_one({'_id': ObjectId(session['uid'])})

        if user_dict:
            g.user = User()
            g.user.update(user_dict)


@app.route('/')
def index():
    clients = Client.get_collection().find(
        {'_id': {'$in': [ObjectId(oid) for oid in g.user.client_ids]}}
    ) if (g.user is not None) else None
    return render_template('index.html', clients=clients)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # if we are already logged in, go back to were we came from
    if g.user is not None:
        return redirect(get_next_url(request))

    error = None
    if request.method == 'POST':
        user = get_valid_user(request.form['email'], request.form['pw'])
        if user:
            session['uid'] = user['_id']
            return redirect(get_next_url(request))
        else:
            error = 'Invalid credentials'

    return render_template('login.html', next=get_next_url(request), error=error)


@app.route('/logout')
def logout():
    session.pop('uid', None)
    flash(u'You have been signed out')
    return redirect(get_next_url(request))
