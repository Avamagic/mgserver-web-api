import time
from werkzeug.exceptions import HTTPException
from flask import json, make_response, request, abort
from flask.ext.restful import reqparse, fields
from ..database import ResourceOwner as User, Client, AccessToken


parser = reqparse.RequestParser()
parser.add_argument("otp", type=int)
parser.add_argument("name", type=str)
parser.add_argument("email", type=str)
parser.add_argument("password", type=str)
parser.add_argument("description", type=str)
parser.add_argument("vendor", type=str)
parser.add_argument("model", type=str)
parser.add_argument("consumer_key", type=str)


def abort_json(code, **kwargs):
    try:
        abort(code)
    except HTTPException as e:
        e.data = kwargs
        raise e


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
    'created_at': Epoch,
    'updated_since': Epoch,
}


def get_user_or_abort():
    if not hasattr(request, "oauth"):
        abort_json(401,
                   flag="fail",
                   msg="Missing OAuth token")
    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        abort_json(401,
                   flag="fail",
                   msg="Access token doesn't associate with any user")
    user_dict = User.find_one({'_id': token['resource_owner_id']})
    user = User()
    user.update(user_dict)
    return user


def get_client_or_abort():
    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        abort_json(404,
                   flag="fail",
                   msg="Access token doesn't associate with any user")
    client = Client.find_one({"_id": token["client_id"]})
    if not client:
        abort_json(404,
                   flag="fail",
                   msg="Access token doesn't associate with any client")
    return client
