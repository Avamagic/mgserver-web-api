from flask import current_app
from flask.ext.login import current_user
from ..extensions import provider, bcrypt
from ..database import ResourceOwner as User, Client
from .exceptions import CreateClientException, SignupException


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

    user_dict = User.find_one({"_id": user_id})
    user = User()
    user.update(user_dict)
    return user


def get_valid_user(email, pw = ""):
    """Return instance of ResourceOwner if credentials are valid
    """
    pw_hash = bcrypt.generate_password_hash(current_app.config['DUMMY_PASSWORD'])
    user_dict = User.find_one({'email': email})
    if user_dict and 'pw_hash' in user_dict:
        pw_hash = user_dict['pw_hash']

    if bcrypt.check_password_hash(pw_hash, pw) and user_dict:
        user = User()
        user.update(user_dict)
        return user
    else:
        return None


def create_client(name, description, callback):
    client = Client.find_one({"resource_owner_id": current_user["_id"], "name": name})
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
        u"resource_owner_id": current_user["_id"],
        u"callbacks": [callback,],
        }
    client = Client(**client_dict)
    client_id = Client.insert(client)
