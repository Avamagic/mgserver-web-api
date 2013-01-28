from functools import wraps
from flask import g, url_for, request, redirect
import datetime, time
from flask.ext.restful import fields


def require_logged_in(f):
    """Require user to be logged in."""
    @wraps(f)
    def decorator(*args, **kwargs):
        if g.user is None:
            next_url = url_for("login") + "?next=" + request.url
            return redirect(next_url)
        else:
            return f(*args, **kwargs)
    return decorator

class Epoch(fields.Raw):
    """Return a Unix time-formatted datetime string in UTC"""
    def format(self, value):
        try:
            return int(time.mktime(value.utctimetuple()))
        except AttributeError as ae:
            raise fields.MarshallingException(ae)
