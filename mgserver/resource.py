from mgserver import app
from flask import flash, render_template, g, session, request
from models import ResourceOwner as User, Client
from provider import ExampleProvider
from bson.objectid import ObjectId
from flask.ext import restful
from flask.ext.restful import reqparse, fields, marshal_with, abort
from flask.ext.bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt(app)
api = restful.Api(app)
provider = ExampleProvider(app)

parser = reqparse.RequestParser()
parser.add_argument('name', type=str)
parser.add_argument('email', type=str)
parser.add_argument('password', type=str)
parser.add_argument('description', type=str)
parser.add_argument('category', type=str)
parser.add_argument('vendor', type=str)
parser.add_argument('model', type=str)

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
    'callback': fields.String,
    'mgserver_id': fields.String,
    'created_at': fields.DateTime,
    'updated_since': fields.DateTime,
}

device_list_fields = {
    'devices': fields.List(fields.Nested(device_fields)),
}


def get_user_or_abort():
    access_token = request.oauth.resource_owner_key
    user = User.find_one({'access_tokens': access_token})
    if not user:
        abort(404, "Access token {} doesn't associate with any user".format(access_token))
    return user


class AnonUser(restful.Resource):
    @marshal_with(user_fields)
    def post(self):
        """Allow anyone to register a new user account."""
        args = parser.parse_args()
        user_dict = {
            u"name": args["name"],
            u"email": args["email"],
            u"pw_hash": bcrypt.generate_password_hash(args["password"]) if args["password"] else None,
        }
        user = User(**user_dict)
        user_id = User.insert(user)
        return User.find_one({'_id': ObjectId(user_id)})


class AuthUser(restful.Resource):
    method_decorators = [provider.require_oauth(realm="admins")]

    @marshal_with(user_fields)
    def get(self, user_id):
        user = User.find_one({'_id': ObjectId(user_id)})
        if not user:
            abort(404, message="User {} doesn't exist".format(user_id))
        return user

    def put(self, user_id):
        user = User.find_one({'_id': ObjectId(user_id)})
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
        User.save(user)
        return user


class DeviceList(restful.Resource):
    method_decorators = [provider.require_oauth(realm=["admins", "users"])]

    @marshal_with(device_fields)
    def post(self):
        user = get_user_or_abort()
        args = parser.parse_args()
        device_dict = {
            u"name": args["name"],
            u"description": args["description"],
            u"category": args["category"],
            u"vendor": args["vendor"],
            u"model": args["model"],
            u"client_key": provider.generate_client_key(),
            u"secret": provider.generate_client_secret(),
        }
        device = Client(**device_dict)
        if args["callback"]:
            device["callbacks"].append(args["callback"])
        device["resource_owner_id"] = user['_id']
        device_id = Client.insert(device)

        user.client_ids.append(device_id)
        User.save(user)

        return Client.find_one({'_id': ObjectId(device_id)})

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


api.add_resource(AnonUser, '/users')
api.add_resource(AuthUser, '/users/<string:user_id>')
api.add_resource(DeviceList, '/devices')
api.add_resource(Device, '/devices/<string:device_id>')
