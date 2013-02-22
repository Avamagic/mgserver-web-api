from flask import url_for
from flask.ext.testing import TestCase as Base
from mgserver import create_app
from mgserver.database import ResourceOwner as User, Client, Device
from mgserver.database import get_db
from mgserver.configs import TestConfig
from mgserver.extensions import provider, bcrypt


class TestCase(Base):
    """Base TestClass for your application."""

    def create_app(self):
        """Create and return a testing flask app."""
        app = create_app(TestConfig)
        return app

    def init_data(self):
        user_dict = {
            u"name": "Known User",
            u"email": "known_user@example.com",
            u"pw_hash": bcrypt.generate_password_hash("9527"),
            }
        user = User(**user_dict)
        User.insert(user)

    def setUp(self):
        """Reset all tables before testing."""
        self.init_data()

    def tearDown(self):
        """Drop all collections."""
        db = get_db()
        for name in db.collection_names():
            if not name.startswith("system."):
                db.drop_collection(name)

    def login(self, email, password):
        data = {
            "email": email,
            "password": password,
        }
        response = self.client.post('/login', data=data, follow_redirects=True)
        return response

    def _logout(self):
        response = self.client.get('/logout')
        self.assert_redirects(response, location=url_for('frontend.index'))

    def _test_get_request(self, endpoint, template=None):
        response = self.client.get(endpoint)
        self.assert_200(response)
        if template:
            self.assert_template_used(name=template)
        return response
