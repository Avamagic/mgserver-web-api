import time
from flask import request, current_app
from flask.ext.restful import reqparse, fields
from ..database import ResourceOwner as User, Client, Device, AccessToken
from .exceptions import ApiException


parser = reqparse.RequestParser()
parser.add_argument("otp", type=int)
parser.add_argument("name", type=str)
parser.add_argument("email", type=str)
parser.add_argument("password", type=str)
parser.add_argument("description", type=str)
parser.add_argument("vendor", type=str)
parser.add_argument("model", type=str)
parser.add_argument("consumer_key", type=str)


class Epoch(fields.Raw):
    """Return a Unix time-formatted datetime string in UTC"""
    def format(self, value):
        try:
            return int(time.mktime(value.utctimetuple()))
        except AttributeError as ae:
            raise fields.MarshallingException(ae)


user_fields = {
    '_id': fields.String,
    'name': fields.String,
    'email': fields.String,
    'client_ids': fields.List(fields.String),
    'device_ids': fields.List(fields.String),
    'created_at': Epoch,
    'updated_since': Epoch,
}


device_fields = {
    '_id': fields.String,
    'name': fields.String,
    'description': fields.String,
    'vendor': fields.String,
    'model': fields.String,
    'mgserver_id': fields.String,
    'access_token_id': fields.String,
    'created_at': Epoch,
    'updated_since': Epoch,
}


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
        Device.insert(device)

        # save back to user instance
        user["device_ids"].append(user["_id"])
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
