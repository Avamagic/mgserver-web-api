from mgserver import app, provider
from flask import flash, render_template, g, session, request
from models import ResourceOwner, Client, AccessToken, Device
from bson.objectid import ObjectId
from flask.ext import restful
from flask.ext.restful import reqparse, fields, marshal_with, abort, marshal
from flask.ext.bcrypt import Bcrypt
from datetime import datetime
import pyotp
import utils

bcrypt = Bcrypt(app)
api = restful.Api(app)

parser = reqparse.RequestParser()
parser.add_argument('otp', type=int)
parser.add_argument('name', type=str)
parser.add_argument('email', type=str)
parser.add_argument('password', type=str)
parser.add_argument('description', type=str)
parser.add_argument('category', type=str)
parser.add_argument('vendor', type=str)
parser.add_argument('model', type=str)
parser.add_argument('callback', type=str)
parser.add_argument('consumer_key', type=str)

user_fields = {
    '_id': fields.String,
    'name': fields.String,
    'email': fields.String,
    'client_ids': fields.List(fields.String),
    'device_ids': fields.List(fields.String),
    'created_at': utils.Epoch,
    'updated_since': utils.Epoch,
}

device_fields = {
    '_id': fields.String,
    'name': fields.String,
    'description': fields.String,
    'vendor': fields.String,
    'model': fields.String,
    'mgserver_id': fields.String,
    'created_at': utils.Epoch,
    'updated_since': utils.Epoch,
}

user_list_fields = {
    'users': fields.List(fields.Nested(user_fields)),
}

def get_user_or_abort():
    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        abort(404, message="Access token doesn't associate with any user")
    user_dict = ResourceOwner.find_one({'_id': token['resource_owner_id']})
    user = ResourceOwner()
    user.update(user_dict)
    return user

def get_client_or_abort():
    access_token = request.oauth.resource_owner_key
    token = AccessToken.find_one({'token': access_token})
    if not token:
        abort(404, message="Access token doesn't associate with any user")
    client = Client.find_one({"_id": token["client_id"]})
    if not client:
        abort(404, message="Access token doesn't associate with any client")
    return client

class Seed(restful.Resource):
    def post(self):
        """Register a new user account."""
        args = parser.parse_args()

        totp = pyotp.TOTP(app.config["OTP_SECRET_KEY"],
                          interval=app.config["OTP_INTERVAL"])
        if not totp.verify(args["otp"]):
            abort(400, message="OTP incorrect, expect {}, got {}".format(totp.now(), args["otp"]))

        # gather user, client and device
        client = Client.find_one({"client_key": args["consumer_key"]})

        user = ResourceOwner()
        user.client_ids.append(client["_id"])
        ResourceOwner.save(user)

        return {
            "user_id": str(user["_id"]),
        }

class UserList(restful.Resource):
    method_decorators = [provider.require_oauth(realm="admins")]

    @marshal_with(user_list_fields)
    def get(self):
        # FIXME: paginate
        users = ResourceOwner.find()
        return users

class User(restful.Resource):
    method_decorators = [provider.require_oauth(realm="admins")]

    @marshal_with(user_fields)
    def get(self, user_id):
        user = ResourceOwner.find_one({'_id': ObjectId(user_id)})
        if not user:
            abort(404, message="User {} doesn't exist".format(user_id))
        return user

    def put(self, user_id):
        user = ResourceOwner.find_one({'_id': ObjectId(user_id)})
        if not user:
            abort(404, message="User {} doesn't exist".format(user_id))

        args = parser.parse_args()
        if args["name"]:
            user["name"] = args["name"]
        if args["email"]:
            user["email"] = args["email"]
        if args["password"]:
            user["pw_hash"] = bcrypt.generate_password_hash(args["password"])
        user["updated_since"] = datetime.utcnow()
        ResourceOwner.save(user)
        return user

class Myself(restful.Resource):
    method_decorators = [provider.require_oauth(realm="users")]

    @marshal_with(user_fields)
    def post(self):
        user = get_user_or_abort()
        args = parser.parse_args()

        if args["name"]:
            user["name"] = args["name"]
        if args["email"]:
            user["email"] = args["email"]
        if args["password"]:
            user["pw_hash"] = bcrypt.generate_password_hash(args["password"])
        user["updated_since"] = datetime.utcnow()
        ResourceOwner.save(user)
        return user

    @marshal_with(user_fields)
    def get(self):
        user = get_user_or_abort()
        return user

class DeviceList(restful.Resource):
    method_decorators = [provider.require_oauth(realm=["admins", "users"])]

    @marshal_with(device_fields)
    def post(self):
        user = get_user_or_abort()
        client = get_client_or_abort()
        args = parser.parse_args()

        device_dict = {
            u"resource_owner_id": user["_id"],
            u"client_id": client["_id"],
            u"vendor": args["vendor"],
            u"model": args["model"],
        }
        device = Device(**device_dict)
        Device.save(device)

        # save back to user
        user.device_ids.append(device["_id"])
        ResourceOwner.save(user)

        return device

    def get(self):
        user = get_user_or_abort()
        devices = Device.find(
            {'_id': {'$in': [oid for oid in user.device_ids]}})
        devices_marshaled = []
        for device in devices:
            devices_marshaled.append(marshal(device, device_fields))
        return {'results': devices_marshaled}

class DeviceRes(restful.Resource):
    method_decorators = [provider.require_oauth(realm="users")]

    @marshal_with(device_fields)
    def get(self, device_id):
        device = Device.find_one({'_id': ObjectId(device_id)})
        if not device:
            abort(404, message="Device {} doesn't exist".format(device_id))
        return device

api.add_resource(Seed, '/v1/seeds')
api.add_resource(UserList, '/v1/users')
api.add_resource(User, '/v1/users/<string:user_id>')
api.add_resource(DeviceList, '/v1/devices')
api.add_resource(DeviceRes, '/v1/devices/<string:device_id>')
api.add_resource(Myself, '/v1/me')
