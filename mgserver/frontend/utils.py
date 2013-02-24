from flask import current_app
from ..extensions import provider, bcrypt
from ..database import ResourceOwner as User, Client
from .exceptions import CreateClientException, SignupException


def create_user(email, passwd="", name=""):
    user = User.find_one({'email': email})
    print user
    if user:
        raise SignupException('This email address is already signed up')

    User.ensure_index("email")

    user_dict = {
        u"email": email,
        u"pw_hash": bcrypt.generate_password_hash(passwd),
        u"name": name,
        }
    user = User(**user_dict)
    User.insert(user)
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


def create_client(user_id, name, description, callback):
    client = Client.find_one({"resource_owner_id": user_id, "name": name})
    if client:
        raise CreateClientException(name)

    Client.ensure_index([("resource_owner_id", 1), ("created_at", -1)])
    Client.ensure_index([("resource_owner_id", 1), ("name", 1)])
    Client.ensure_index("client_key")
    Client.ensure_index("name")

    client_dict = {
        u"name": name,
        u"description": description,
        u"client_key": provider.generate_client_key(),
        u"secret": provider.generate_client_secret(),
        u"resource_owner_id": user_id,
        u"callbacks": [callback,],
        }
    client = Client(**client_dict)
    Client.insert(client)
    return client
