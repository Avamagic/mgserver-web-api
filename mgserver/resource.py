from mgserver import app
from flask import flash, render_template, g, session, request
from models import ResourceOwner, Client, AccessToken
from provider import ExampleProvider
from bson.objectid import ObjectId
from flask.ext import restful
from flask.ext.restful import reqparse, fields, marshal_with, abort
from flask.ext.bcrypt import Bcrypt
from datetime import datetime
import pyotp

bcrypt = Bcrypt(app)
api = restful.Api(app)
provider = ExampleProvider(app)

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

user_fields = {
    '_id': fields.String,
    'name': fields.String,
    'email': fields.String,
    'client_ids': fields.List(fields.String),
    'created_at': fields.DateTime,
    'updated_since': fields.DateTime,
}

device_fields = {
    '_id': fields.String,
    'name': fields.String,
    'description': fields.String,
    'category': fields.String,
    'vendor': fields.String,
    'model': fields.String,
    'callbacks': fields.List(fields.String),
    'mgserver_id': fields.String,
    'created_at': fields.DateTime,
    'updated_since': fields.DateTime,
}

user_list_fields = {
    'users': fields.List(fields.Nested(user_fields)),
}

device_list_fields = {
    'devices': fields.List(fields.Nested(device_fields)),
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


def create_user():
    user = ResourceOwner()
    user_id = ResourceOwner.insert(user)
    return user_id


def create_client(resource_owner_id, category, vendor, model, callback):
    device_dict = {
        u"category": category,
        u"vendor": vendor,
        u"model": model,
        u"client_key": provider.generate_client_key(),
        u"secret": provider.generate_client_secret(),
        u"resource_owner_id": resource_owner_id,
    }
    device = Client(**device_dict)
    device["callbacks"].append(callback)
    device_id = Client.insert(device)
    return device_id


class Seed(restful.Resource):
    def post(self):
        """Register a new user account and the initial client."""
        args = parser.parse_args()

        totp = pyotp.TOTP(app.config["OTP_SECRET_KEY"])
        if not totp.verify(args["otp"]):
            abort(400, message="OTP incorrect")

        user_id = create_user()
        device_id = create_client(
            user_id,
            args["category"], args["vendor"], args["model"],
            args["callback"]
        )

        # add client to user
        user_dict = ResourceOwner.find_one({'_id': user_id})
        user = ResourceOwner()
        user.update(user_dict)
        user.client_ids.append(device_id)
        ResourceOwner.save(user)

        device_dict = Client.find_one({'_id': device_id})
        client_key = device_dict["client_key"]
        client_secret = device_dict["secret"]

        return {
            "uid": str(user_id),
            "client_key": client_key,
            "secret": client_secret,
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
            user["pw_hash"] = bcrypt.generate_password_hash(args["password"]),
        user["updated_since"] = datetime.utcnow()
        ResourceOwner.save(user)
        return user


class Myself(restful.Resource):
    method_decorators = [provider.require_oauth(realm="users")]

    @marshal_with(user_fields)
    def get(self):
        user = get_user_or_abort()
        return user


class DeviceList(restful.Resource):
    method_decorators = [provider.require_oauth(realm=["admins", "users"])]

    @marshal_with(device_fields)
    def post(self):
        user = get_user_or_abort()
        args = parser.parse_args()

        device_id = create_client(
            user['_id'],
            args["category"], args["vendor"], args["model"],
            args["callback"]
        )

        user.client_ids.append(device_id)
        ResourceOwner.save(user)

        return Client.find_one({'_id': device_id})

    @marshal_with(device_list_fields)
    def get(self):
        user = get_user_or_abort()
        clients = Client.get_collection().find(
            {'_id': {'$in': [ObjectId(oid) for oid in user.client_ids]}})
        return clients


class Device(restful.Resource):
    method_decorators = [provider.require_oauth(realm="users")]

    @marshal_with(device_fields)
    def get(self, device_id):
        device = Client.find_one({'_id': ObjectId(device_id)})
        if not device:
            abort(404, message="Device {} doesn't exist".format(device_id))
        return device


api.add_resource(Seed, '/v1/seeds')
api.add_resource(UserList, '/v1/users')
api.add_resource(User, '/v1/users/<string:user_id>')
api.add_resource(DeviceList, '/v1/devices')
api.add_resource(Device, '/v1/devices/<string:device_id>')
api.add_resource(Myself, '/v1/me')
