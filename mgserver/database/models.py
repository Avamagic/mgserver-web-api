from flask import current_app
import pymongo
from datetime import datetime
import uuid


def get_db():
    connection = pymongo.MongoClient(current_app.config['MONGO_HOST'],
                                     current_app.config['MONGO_PORT'])
    return connection[current_app.config['MONGO_DATABASE']]


class Model(dict):
    @classmethod
    def get_collection(cls):
        db = get_db()
        return db[cls.table]

    @classmethod
    def find_one(cls, attrs):
        return cls.get_collection().find_one(attrs)

    @classmethod
    def find(cls, attrs):
        return cls.get_collection().find(attrs)

    @classmethod
    def insert(cls, obj):
        return cls.get_collection().insert(obj)

    @classmethod
    def save(cls, obj):
        return cls.get_collection().save(obj)

    @classmethod
    def ensure_index(cls, key_or_list):
        return cls.get_collection().ensure_index(key_or_list)

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value


class ResourceOwner(Model):
    table = "users"

    def __init__(self, name="", email="", pw_hash=""):
        now = datetime.utcnow()

        self.name = name
        self.email = email
        self.pw_hash = pw_hash

        self.created_at = now
        self.updated_since = now

        self.request_tokens = []
        self.access_tokens = []
        self.client_ids = []
        self.device_ids = []

    def __repr__(self):
        return "<ResourceOwner (%s, %s)>" % (self.name, self.email)

    def is_authenticated(self):
        return '_id' in self

    def is_active(self):
        return self.is_authenticated()

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self['_id']) if ('_id' in self) else None


class Client(Model):
    table = "clients"

    def __init__(self, client_key, secret, callbacks, resource_owner_id, name, description):
        now = datetime.utcnow()

        self.name = name
        self.description = description

        self.created_at = now
        self.updated_since = now

        self.client_key = client_key
        self.secret = secret
        self.request_tokens = []
        self.access_tokens = []
        self.callbacks = callbacks
        self.resource_owner_id = resource_owner_id

    def __repr__(self):
        return "<Client (%s, %s)>" % (self.name, self.id)


class Device(Model):
    table = "devices"

    def __init__(self,
                 access_token_id,
                 vendor="", model="",
                 features=[],
                 name="", description=""):
        now = datetime.utcnow()

        self.name = name
        self.description = description
        self.vendor = vendor
        self.model = model
        self.features = []
        self.access_token_id = access_token_id

        self.mgserver_id = uuid.uuid4()
        self.created_at = now
        self.updated_since = now

    def __repr__(self):
        return "<Device (%s, %s)>" % (self.name, self.id)


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
