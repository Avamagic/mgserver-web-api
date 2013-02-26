from flask import request, current_app
from ..common import ApiException, CreateClientException, SignupException
from .models import ResourceOwner as User, Client, Device, AccessToken


def create_user(email, passwd="", name=""):
    user = User.find_one({'email': email})
    if user:
        raise SignupException('This email address is already signed up')

    User.ensure_index("email")

    # HACK: this is for avoiding recursive import
    from ..extensions import bcrypt
    user_dict = {
        u"email": email,
        u"pw_hash": bcrypt.generate_password_hash(passwd),
        u"name": name,
        }
    user = User(**user_dict)
    User.save(user)

    return user


def create_client(user, name, description, callback):
    client = Client.find_one({"resource_owner_id": user["_id"], "name": name})
    if client:
        raise CreateClientException(name)

    Client.ensure_index([("resource_owner_id", 1), ("created_at", -1)])
    Client.ensure_index([("resource_owner_id", 1), ("name", 1)])
    Client.ensure_index("client_key")
    Client.ensure_index("name")

    # HACK: this is for avoiding recursive import
    from ..extensions import provider
    client_dict = {
        u"name": name,
        u"description": description,
        u"client_key": provider.generate_client_key(),
        u"secret": provider.generate_client_secret(),
        u"resource_owner_id": user["_id"],
        u"callbacks": [callback,],
        }
    client = Client(**client_dict)
    Client.save(client)

    # save back to user
    user["client_ids"].append(client["_id"])
    User.save(user)

    return client


def get_or_create_device(access_token):
    device = Device.find_one({"access_token_id": access_token["_id"]})
    if not device:
        user = User.find_one({"_id": access_token["resource_owner_id"]})
        if not user:
            raise ApiException(
                code=404,
                msg="User not associated with access token",
                )

        Device.ensure_index("access_token_id")
        device_dict = {"access_token_id": access_token["_id"]}
        device = Device(**device_dict)
        Device.save(device)

        # save back to user instance
        user["device_ids"].append(device["_id"])
        User.save(user)
    return device


def get_user_or_abort():
    if "TESTING_WITHOUT_OAUTH" in current_app.config:
        return current_app.config["TESTING_WITHOUT_OAUTH"]["known_user"]

    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        raise ApiException(
            code=401,
            msg="Access token doesn't associate with any user",
            )
    user_dict = User.find_one({'_id': token['resource_owner_id']})
    user = User()
    user.update(user_dict)
    return user


def get_client_or_abort():
    if "TESTING_WITHOUT_OAUTH" in current_app.config:
        return current_app.config["TESTING_WITHOUT_OAUTH"]["known_client"]

    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        raise ApiException(
            code=404,
            msg="Access token doesn't associate with any user",
            )
    client = Client.find_one({"_id": token["client_id"]})
    if not client:
        raise ApiException(
            code=404,
            msg="Access token doesn't associate with any client",
            )
    return client


def get_device_or_abort():
    if "TESTING_WITHOUT_OAUTH" in current_app.config:
        return current_app.config["TESTING_WITHOUT_OAUTH"]["known_device"]

    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        raise ApiException(
            code=404,
            msg="Access token doesn't associate with any user",
            )
    return get_or_create_device(token)
