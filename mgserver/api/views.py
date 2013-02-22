from flask import Blueprint, request, abort, jsonify
from flask.views import MethodView
from flask.ext.restful import marshal
from bson.objectid import ObjectId
from datetime import datetime
import pyotp
from ..extensions import bcrypt, provider
from ..database import ResourceOwner as User, Client, Device
from .utils import (parser, user_fields, device_fields,
                    get_user_or_abort, get_client_or_abort,
                    abort_json)


api = Blueprint("api", __name__)


class Seed(MethodView):

    def post(self):
        """Register a new user account."""
        args = parser.parse_args()

        totp = pyotp.TOTP(current_app.config["OTP_SECRET_KEY"],
                          interval=current_app.config["OTP_INTERVAL"])
        if not totp.verify(args["otp"]):
            abort_json(400,
                       flag="fail",
                       msg="OTP incorrect, expect {}, got {}".format(totp.now(), args["otp"]))

        # gather user, client and device
        client = Client.find_one({"client_key": args["consumer_key"]})

        user = User()
        user.client_ids.append(client["_id"])
        User.save(user)

        return jsonify({
                "flag": "success",
                "user_id": str(user["_id"]),
                })


class Myself(MethodView):

    method_decorators = [provider.require_oauth(realm="users")]

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
        User.save(user)

        return jsonify({
                "flag": "success",
                "res": marshal(user, user_fields),
                })

    def get(self):
        user = get_user_or_abort()
        return jsonify({
                "flag": "success",
                "res": marshal(user, user_fields),
                })


class DeviceList(MethodView):

    method_decorators = [provider.require_oauth(realm="users")]

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
        User.save(user)

        return jsonify({
                "flag": "success",
                "res": marshal(device, device_fields),
                })

    def get(self):
        user = get_user_or_abort()
        devices = Device.find(
            {'_id': {'$in': [oid for oid in user.device_ids]}})
        devices_marshaled = []
        for device in devices:
            devices_marshaled.append(marshal(device, device_fields))
        return jsonify({
                "flag": "success",
                "res": devices_marshaled,
                })


class DeviceRes(MethodView):

    method_decorators = [provider.require_oauth(realm="users")]

    def get(self, device_id):
        device = Device.find_one({'_id': ObjectId(device_id)})
        if not device:
            abort_json(404,
                       flag="fail",
                       msg="Device {} doesn't exist".format(device_id))
        return jsonify({
                "flag": "success",
                "res": marshal(device, device_fields),
                })


api.add_url_rule("/v1/seeds",
                 view_func=Seed.as_view("seeds"))
api.add_url_rule("/v1/devices",
                 view_func=DeviceList.as_view("devices"))
api.add_url_rule("/v1/devices/<string:device_id>",
                 view_func=DeviceRes.as_view("device"))
api.add_url_rule("/v1/me",
                 view_func=Myself.as_view("myself"))
