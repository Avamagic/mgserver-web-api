import time
from flask.ext.restful import reqparse, fields


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
