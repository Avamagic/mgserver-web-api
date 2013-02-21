from flask import Flask
from bson.objectid import ObjectId
from .configs import DevConfig
from .frontend import frontend
from .api import api
from .extensions import provider, login_manager, bcrypt
from .database.models import ResourceOwner as User


# For import *
__all__ = ['create_app']


DEFAULT_BLUEPRINTS = (
    frontend,
    api,
    )


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = DevConfig.PROJECT
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name)
    configure_app(app, config)
    configure_hook(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_template_filters(app)

    return app


def configure_app(app, config):
    """Configure app from object, parameter and env."""

    app.config.from_object(DevConfig)
    if config is not None:
        app.config.from_object(config)
    # Override setting by env var without touching codes.
    app.config.from_envvar('%s_APP_CONFIG' % DevConfig.PROJECT.upper(), silent=True)


def configure_hook(app):
    @app.before_request
    def before_request():
        pass


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_extensions(app):
    # flask-bcrypt
    bcrypt.init_app(app)

    # flask-oauthprovider
    provider.init_app(app)

    # flask-login
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(userid):
        user_dict = User.find_one({'_id': ObjectId(userid)})
        if user_dict:
            user = User()
            user.update(user_dict)
            return user
        else:
            return None

    login_manager.setup_app(app)


def configure_template_filters(app):

    @app.template_filter()
    def datetimeformat(value, format="%Y-%d-%m %H:%M"):
        return value.strftime(format)
