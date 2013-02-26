import pymongo
from flask import url_for
from flask.ext.testing import TestCase as Base
from flask.ext.restful import marshal
from mgserver import create_app
from mgserver.configs import TestConfig
from mgserver.api import user_fields, device_fields
from mgserver.database import ResourceOwner as User, AccessToken, Device
from mgserver.database import create_user, create_client
from mgserver.database import get_or_create_device


def create_access_token(token, user, client):
    token = AccessToken(token="known_token")
    token["resource_owner_id"] = user["_id"]
    token["client_id"] = client["_id"]
    AccessToken.save(token)

    user["access_tokens"].append(token["_id"])
    User.save(user)

    return token


class TestCase(Base):
    """Base TestClass for your application."""

    def create_app(self):
        """Create and return a testing flask app."""
        app = create_app(TestConfig)
        return app

    def init_data(self):
        user = create_user(
            "known_user@example.com",
            "9527",
            "Known User"
            )

        client = create_client(
            user,
            "Known app",
            "Official known app for testing",
            "known://fake/app"
            )
        self.known_client = client

        access_token = create_access_token(
            "known_token",
            user,
            client,
            )
        self.known_access_token = access_token

        device = get_or_create_device(access_token)
        self.known_device = device
        self.known_device_marshalled = marshal(device, device_fields)

        # fetch user again, since it might be modified
        user_dict = User.find_one({"_id": user["_id"]})
        user = User()
        user.update(user_dict)
        self.known_user = user
        self.known_user_marshalled = marshal(user, user_fields)

    def setUp(self):
        """Reset all tables before testing."""
        connection = pymongo.MongoClient(self.app.config["MONGO_HOST"],
                                         self.app.config["MONGO_PORT"])
        connection.drop_database(self.app.config["MONGO_DATABASE"])
        self.init_data()

    def tearDown(self):
        """Drop unittesting database."""
        connection = pymongo.MongoClient(self.app.config["MONGO_HOST"],
                                         self.app.config["MONGO_PORT"])
        connection.drop_database(self.app.config["MONGO_DATABASE"])

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
