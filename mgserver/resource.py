from mgserver import app
from flask import flash, render_template, g, session, request
from models import ResourceOwner as User
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
    'name': fields.String,
    'email': fields.String,
    'client_ids': fields.List(fields.String),
    'created_at': fields.DateTime,
    'updated_since': fields.DateTime,
}

device_fields = {
    'name': fields.String,
    'description': fields.String,
    'category': fields.String,
    'vendor': fields.String,
    'model': fields.String,
    'mgserver_id': fields.String,
    'created_at': fields.DateTime,
    'updated_since': fields.DateTime,
}


class AnonUser(restful.Resource):
    @marshal_with(user_fields)
    def post(self):
        """Allow anyone to register a new user account."""
        args = parser.parse_args()
        user_dict = {
            u"name": args["name"],
            u"email": args["email"],
            u"pw_hash": bcrypt.generate_password_hash(args["password"]),
        }
        user = User(**user_dict)
        user_id = User.insert(user)
        return User.find_one({'_id': ObjectId(user_id)})

class AuthUser(restful.Resource):
    method_decorators = [provider.require_oauth(realm="users")]

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


api.add_resource(AnonUser, '/users')
api.add_resource(AuthUser, '/users/<string:user_id>')
