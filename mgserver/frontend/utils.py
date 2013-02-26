from flask import current_app
from ..extensions import bcrypt
from ..database import ResourceOwner as User


def get_valid_user(email, pw = ""):
    """Return instance of ResourceOwner if credentials are valid
    """
    pw_hash = bcrypt.generate_password_hash(current_app.config['DUMMY_PASSWORD'])
    user_dict = User.find_one({'email': email})
    if user_dict and 'pw_hash' in user_dict:
        pw_hash = user_dict['pw_hash']

    if bcrypt.check_password_hash(pw_hash, pw) and user_dict:
        user = User()
        user.update(user_dict)
        return user
    else:
        return None
