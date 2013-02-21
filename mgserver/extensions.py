from .database.provider import MongoProvider
provider = MongoProvider()

from flask.ext.login import LoginManager
login_manager = LoginManager()

from flask.ext.bcrypt import Bcrypt
bcrypt = Bcrypt()
