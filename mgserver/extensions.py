from .database import MongoProvider
provider = MongoProvider(None)

from flask.ext.login import LoginManager
login_manager = LoginManager()

from flask.ext.bcrypt import Bcrypt
bcrypt = Bcrypt()

import pyotp
class MGTotp:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.totp = pyotp.TOTP(app.config["OTP_SECRET_KEY"],
                               app.config["OTP_INTERVAL"])

    def verify(self, code):
        return self.totp.verify(code)

    def now(self):
        return self.totp.now()

totp = MGTotp()
