from flask import url_for
from flask.ext.testing import TestCase as Base
from mgserver import create_app
from mgserver.database import get_db
from mgserver.configs import TestConfig
from mgserver.frontend.utils import create_user, create_client


class TestCase(Base):
    """Base TestClass for your application."""

    def create_app(self):
        """Create and return a testing flask app."""
        app = create_app(TestConfig)
        return app

    def init_data(self):
        self.known_user = create_user(
            "known_user@example.com",
            "9527",
            "Known User"
            )

        self.known_client = create_client(
            self.known_user["_id"],
            "Known app",
            "Official known app for testing",
            "known://fake/app"
            )

    def setUp(self):
        """Reset all tables before testing."""
        self.init_data()

    def tearDown(self):
        """Drop all collections."""
        db = get_db()
        for name in db.collection_names():
            if not name.startswith("system."):
                db.drop_collection(name)

    def login(self, email, password, follow_redirects=True):
        data = {
            "email": email,
            "password": password,
            }
        response = self.client.post('/login',
                                    data=data,
                                    follow_redirects=follow_redirects)
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
