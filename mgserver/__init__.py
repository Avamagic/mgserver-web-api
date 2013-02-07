from flask import Flask, request
from provider import ExampleProvider
from models import AccessToken, ResourceOwner as User

app = Flask(__name__)
app.config.update(
    DEBUG = True,
    TESTING = False,
    MONGO_HOST = "localhost",
    MONGO_PORT = 27017,
    SECRET_KEY = "debugging key",
    DUMMY_EMAIL = "dummy@example.com",
    DUMMY_PASSWORD = "dummyhash321",
    OTP_SECRET_KEY = "base32secret3232", # use pyotp.random_base32() to generate
    OTP_INTERVAL = 3600, # one hour?! this must match with client
)
app.config.from_pyfile('custom.cfg', True)

provider = ExampleProvider(app)

# Imported to setup views
import login
import resource
import ui

@app.route('/callback')
def callback():
    return str(request.__dict__)

@app.route("/protected")
@provider.require_oauth()
def protected_view():
    token = request.oauth.resource_owner_key
    access_token = AccessToken.get_collection().find_one({'token':token})
    user = User.find_one({'_id':access_token['resource_owner_id']})
    return user['name']


@app.route("/protected_realm")
@provider.require_oauth(realm="users")
def protected_realm_view():
    token = request.oauth.resource_owner_key
    access_token = AccessToken.get_collection().find_one({'token':token})
    user = User.find_one({'_id':access_token['resource_owner_id']})
    return user['email']
