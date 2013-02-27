from functools import wraps
from flask import Blueprint, request, abort, jsonify
from flask import make_response, json, current_app
from flask.views import MethodView
from flask.ext.restful import marshal
from bson.objectid import ObjectId
from datetime import datetime
import pyotp
from ..common import ApiException
from ..extensions import bcrypt, provider, totp
from ..database import ResourceOwner as User, Client, Device
from ..database import get_user_or_abort, get_client_or_abort, get_device_or_abort
from .utils import parser, user_fields, device_fields


api = Blueprint("api", __name__)


@api.errorhandler(ApiException)
def handle_api_exception(error):
    data = {
        "flag": "fail",
        "msg": error.msg,
        }
    resp = make_response(json.dumps(data), error.code)
    resp.headers["Content-Type"] = "application/json"
    return resp


def require_oauth(f):
    @wraps(f)
    def deco(*args, **kwargs):
        if "TESTING_WITHOUT_OAUTH" in current_app.config:
            return f(*args, **kwargs)
        else:
            decorator = provider.require_oauth(realm="users")
            meth = decorator(f)
            return meth(*args, **kwargs)
    return deco


class Seed(MethodView):

    def post(self):
        """Register a new user account."""
        args = parser.parse_args()

        if not totp.verify(args["otp"]):
            raise ApiException(
                code=400,
                msg="OTP incorrect, expect {}, got {}".format(totp.now(), args["otp"]),
                )

        # gather user, client and device
        client = Client.find_one({"client_key": args["consumer_key"]})
        if not client:
            raise ApiException(
                code=400,
                msg="Client key not found: {}".format(args["consumer_key"]),
                )

        user = User()
        user.client_ids.append(client["_id"])
        User.save(user)

        return jsonify({
                "flag": "success",
                "user_id": str(user["_id"]),
                })


class Myself(MethodView):

    decorators = [require_oauth]

    def put(self):
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

    decorators = [require_oauth]

    def put(self, device_id):
        if device_id is None:
            raise ApiException(
                code=400,
                msg="Does not support updating multiple devices",
                )
        elif device_id == "from_access_token":
            device = get_device_or_abort()
        else:
            device = Device.find_one({'_id': ObjectId(device_id)})
            if not device:
                raise ApiException(
                    code=404,
                    msg="Device {} doesn't exist".format(device_id),
                    )

        args = parser.parse_args()

        if args["name"]:
            device["name"] = args["name"]
        if args["description"]:
            device["description"] = args["description"]
        if args["vendor"]:
            device["vendor"] = args["vendor"]
        if args["model"]:
            device["model"] = args["model"]
        device["updated_since"] = datetime.utcnow()
        Device.save(device)

        return jsonify({
                "flag": "success",
                "res": marshal(device, device_fields),
                })

    def get(self, device_id):
        if device_id is None:
            user = get_user_or_abort()
            devices = Device \
                .find({'_id': {'$in': [oid for oid in user.device_ids]}}) \
                .sort('updated_since', -1)
            devices_marshaled = []
            for device in devices:
                devices_marshaled.append(marshal(device, device_fields))
            return jsonify({
                    "flag": "success",
                    "res": devices_marshaled,
                    })
        elif device_id == "from_access_token":
            device = get_device_or_abort()
            return jsonify({
                    "flag": "success",
                    "res": marshal(device, device_fields),
                    })
        else:
            device = Device.find_one({'_id': ObjectId(device_id)})
            if not device:
                raise ApiException(
                    code=404,
                    msg="Device {} doesn't exist".format(device_id),
                    )
            return jsonify({
                    "flag": "success",
                    "res": marshal(device, device_fields),
                    })


api.add_url_rule("/v1/seeds",
                 view_func=Seed.as_view("seeds"))

device_list_view = DeviceList.as_view("devices")
api.add_url_rule("/v1/devices",
                 defaults={"device_id": None},
                 view_func=device_list_view,
                 methods=["GET",])
api.add_url_rule("/v1/devices/<string:device_id>",
                 view_func=device_list_view,
                 methods=["GET", "PUT"])
api.add_url_rule("/v1/device",
                 defaults={"device_id": "from_access_token"},
                 view_func=device_list_view,
                 methods=["GET", "PUT"])

api.add_url_rule("/v1/me",
                 view_func=Myself.as_view("myself"),
                 methods=["GET", "PUT"])
