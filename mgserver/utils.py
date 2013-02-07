from functools import wraps
from flask import g, url_for, request, redirect
import datetime, time
from flask.ext.restful import fields
from urlparse import urlparse, urljoin
from flask.ext.wtf import Form, TextField, HiddenField


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

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))
