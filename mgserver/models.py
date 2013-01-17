import pymongo


def get_db():
    from mgserver import app
    connection = pymongo.MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
    return connection.mgserver_oauth_provider


class Model(dict):
    @classmethod
    def get_collection(cls):
        db = get_db()
        return db[cls.table]

    @classmethod
    def find_one(cls, attrs):
        return cls.get_collection().find_one(attrs)

    @classmethod
    def insert(cls, obj):
        return cls.get_collection().insert(obj)

    @classmethod
    def save(cls, obj):
        return cls.get_collection().save(obj)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


class ResourceOwner(Model):
    table = "users"

    def __init__(self, name="", email="", pw_hash=""):
        self.name = name
        self.email = email
        self.pw_hash = pw_hash
        self.request_tokens = []
        self.access_tokens = []
        self.client_ids = []

    def __repr__(self):
        return "<ResourceOwner (%s, %s)>" % (self.name, self.email)


class Client(Model):
    table = "clients"

    def __init__(self, client_key, mgserver_id, name, description, category, vendor, model, secret=None, pubkey=None):
        self.client_key = client_key
        self.mgserver_id = mgserver_id
        self.name = name
        self.description = description
        self.category = category
        self.vendor = vendor
        self.model = model
        self.secret = secret
        self.pubkey = pubkey
        self.request_tokens = []
        self.access_tokens = []
        self.callbacks = []
        self.resource_owner_id = ""

    def __repr__(self):
        return "<Client (%s, %s)>" % (self.name, self.id)


class Nonce(Model):
    table = "nonces"

    def __init__(self, nonce, timestamp):
        self.nonce = nonce
        self.timestamp = timestamp
        self.client_id = ""
        self.request_token_id = ""
        self.access_token_id = ""

    def __repr__(self):
        return "<Nonce (%s, %s, %s, %s)>" % (self.nonce, self.timestamp, self.client, self.resource_owner)


class RequestToken(Model):
    table = "requestTokens"

    def __init__(self, token, callback, secret=None, verifier=None, realm=None):
        self.token = token
        self.secret = secret
        self.verifier = verifier
        self.realm = realm
        self.callback = callback
        self.client_id = ""
        self.resource_owner_id = ""


    def __repr__(self):
        return "<RequestToken (%s, %s, %s)>" % (self.token, self.client, self.resource_owner)


class AccessToken(Model):
    table = "accessTokens"

    def __init__(self, token, secret=None, verifier=None, realm=None):
        self.token = token
        self.secret = secret
        self.verifier = verifier
        self.realm = realm
        self.client_id = ""
        self.resource_owner_id = ""

    def __repr__(self):
        return "<AccessToken (%s, %s, %s)>" % (self.token, self.client, self.resource_owner)
