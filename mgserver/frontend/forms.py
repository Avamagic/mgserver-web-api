from urlparse import urlparse, urljoin
from flask import request, redirect
from flask.ext.wtf import Form
from flask.ext.wtf import HiddenField, BooleanField, TextField, PasswordField
from flask.ext.wtf import Required, Length, EqualTo, Email, URL


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


class LoginForm(RedirectForm):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    remember = BooleanField('Remember me')


class SignupForm(RedirectForm):
    name = TextField('Name', [Required()])
    email = TextField('Email address', [Email()])
    password = PasswordField('Password', [
            Required(),
            EqualTo('confirm', message='Passwords must match')
            ])
    confirm = PasswordField('Repeat password')


class ClientForm(Form):
    name = TextField('Name', [Required()])
    description = TextField('Description')
    callback = TextField('Callback', [Required(), URL(require_tld=False)])
