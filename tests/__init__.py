import pymongo
from flask import url_for
from flask.ext.testing import TestCase as Base
from flask.ext.restful import marshal
from mgserver import create_app
from mgserver.configs import TestConfig
from mgserver.frontend import create_user, create_client
from mgserver.api import user_fields, device_fields
from mgserver.database import ResourceOwner as User, AccessToken, Device


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
            user["_id"],
            "Known app",
            "Official known app for testing",
            "known://fake/app"
            )
        self.known_client = client

        access_token = AccessToken(token="known_token")
        access_token["resource_owner_id"] = user["_id"]
        access_token["client_id"] = client["_id"]
        AccessToken.save(access_token)
        self.known_access_token = access_token

        device = Device(access_token_id=access_token["_id"])
        Device.save(device)
        self.known_device = device
        self.known_device_marshalled = marshal(self.known_device, device_fields)

        user["client_ids"].append(client["_id"])
        user["device_ids"].append(device["_id"])
        user["access_tokens"].append(access_token["_id"])
        User.save(user)
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
