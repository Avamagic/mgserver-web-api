import os


class BaseConfig(object):

    # Get app root path
    # ../../configs/config.py
    _basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    PROJECT = "mgserver"
    DEBUG = False
    TESTING = False

    ADMINS = frozenset(['ronhuang@avamagic.com'])

    # os.urandom(24)
    SECRET_KEY = 'secret key'

    MONGO_HOST = "localhost"
    MONGO_PORT = 27017
    MONGO_DATABASE = "mgserver_oauth_provider"

    DUMMY_EMAIL = "dummy@example.com"
    DUMMY_PASSWORD = "dummyhash321"

    OTP_SECRET_KEY = "base32secret3232" # use pyotp.random_base32() to generate
    OTP_INTERVAL = 3600 # one hour?! this must match with client


class DevConfig(BaseConfig):

    DEBUG = True

    # ===========================================
    # Flask-babel
    #
    ACCEPT_LANGUAGES = ['zh']
    BABEL_DEFAULT_LOCALE = 'en'

    # ===========================================
    # Flask-cache
    #
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 60

    # ===========================================
    # Flask-mail
    #
    # Should be imported from env var.
    # https://bitbucket.org/danjac/flask-mail/issue/3/problem-with-gmails-smtp-server
    MAIL_DEBUG = DEBUG
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'gmail_username'
    MAIL_PASSWORD = 'gmail_password'
    DEFAULT_MAIL_SENDER = '%s@gmail.com' % MAIL_USERNAME


class TestConfig(BaseConfig):

    TESTING = True

    CSRF_ENABLED = False

    MONGO_DATABASE = "mgserver_unittest"
