from datetime import datetime
from bson.objectid import ObjectId
from flask.ext.restful import fields
from mgserver.common import ApiException
from mgserver.extensions import provider, totp
from mgserver.api import Epoch
from tests import TestCase, TestCaseWithoutAuth


class TestViews(TestCase):

    def setUp(self):
        super(TestViews, self).setUp()

        self.app.config["TESTING_WITHOUT_OAUTH"] = {
            "known_user": self.known_user,
            "known_client": self.known_client,
            "known_device": self.known_device,
            }

    def test_seed(self):
        data = {
            "otp": str(totp.now()),
            "consumer_key": self.known_client["client_key"],
            }
        response = self.client.post("/v1/seeds", data=data)
        seed = response.json

        assert "success" == seed["flag"]
        assert str(self.known_user["_id"]) != seed["user_id"]

    def test_seed_invalid_otp(self):
        data = {
            "otp": "1111111111",
            "consumer_key": self.known_client["client_key"],
            }
        response = self.client.post("/v1/seeds", data=data)
        seed = response.json

        assert "fail" == seed["flag"]
        assert "OTP incorrect" in seed["msg"]

    def test_seed_invalid_client_key(self):
        data = {
            "otp": str(totp.now()),
            "consumer_key": "111234567",
            }
        response = self.client.post("/v1/seeds", data=data)
        seed = response.json

        assert "fail" == seed["flag"]
        assert "Client key not found" in seed["msg"]

    def test_myself_get(self):
        resp = self.client.get("/v1/me")

        assert "success" == resp.json["flag"]
        assert str(self.known_user["_id"]) == resp.json["res"]["_id"]

    def test_myself_put(self):
        old_timestamp = self.known_user_marshalled["updated_since"]
        data = {
            "name": "My New Awesome Name",
            "email": "my_new_awesome_email@example.com",
            }
        resp = self.client.put("/v1/me", data=data)

        assert "success" == resp.json["flag"]
        assert str(self.known_user["_id"]) == resp.json["res"]["_id"]
        assert resp.json["res"]["name"] == data["name"]
        assert resp.json["res"]["email"] == data["email"]
        assert resp.json["res"]["updated_since"] >= old_timestamp

    def test_myself_post_not_allowed(self):
        data = {
            "name": "My New Awesome Name",
            "email": "my_new_awesome_email@example.com",
            }
        resp = self.client.post("/v1/me", data=data)

        self.assert_405(resp)

    def test_devices_get_all(self):
        resp = self.client.get("/v1/devices")
        assert "success" == resp.json["flag"]

        devices = resp.json["res"]
        assert len(devices) == 1

        device = devices[0]
        assert str(self.known_device["_id"]) == str(device["_id"])
        assert str(self.known_access_token["_id"]) == str(device["access_token_id"])

    def test_device_get_from_token(self):
        resp = self.client.get("/v1/device")
        assert "success" == resp.json["flag"]

        device = resp.json["res"]
        assert str(self.known_device["_id"]) == device["_id"]
        assert str(self.known_access_token["_id"]) == device["access_token_id"]

    def test_device_get_from_id(self):
        resp = self.client.get("/v1/devices/{}".format(str(self.known_device["_id"])))
        assert "success" == resp.json["flag"]

        device = resp.json["res"]
        assert str(self.known_device["_id"]) == device["_id"]
        assert str(self.known_access_token["_id"]) == device["access_token_id"]

    def test_device_put_with_token(self):
        old_timestamp = self.known_device_marshalled["updated_since"]
        data = {
            "name": "My New Awesome Name",
            "description": "My new not so awesome description",
            "vendor": "Avamagic",
            "model": "MGServer Client",
            }
        resp = self.client.put("/v1/device", data=data)

        assert "success" == resp.json["flag"]
        device = resp.json["res"]
        assert str(self.known_device["_id"]) == device["_id"]
        assert device["name"] == data["name"]
        assert device["description"] == data["description"]
        assert device["vendor"] == data["vendor"]
        assert device["model"] == data["model"]
        assert device["updated_since"] >= old_timestamp

    def test_device_put_with_id(self):
        old_timestamp = self.known_device_marshalled["updated_since"]
        data = {
            "name": "My New Awesome Name",
            "description": "My new not so awesome description",
            "vendor": "Avamagic",
            "model": "MGServer Client",
            }
        resp = self.client.put("/v1/devices/{}".format(str(self.known_device["_id"])),
                               data=data)

        assert "success" == resp.json["flag"]
        device = resp.json["res"]
        assert str(self.known_device["_id"]) == device["_id"]
        assert device["name"] == data["name"]
        assert device["description"] == data["description"]
        assert device["vendor"] == data["vendor"]
        assert device["model"] == data["model"]
        assert device["updated_since"] >= old_timestamp

    def test_device_put_nonexist(self):
        old_timestamp = self.known_device_marshalled["updated_since"]
        data = {
            "name": "My New Awesome Name",
            "description": "My new not so awesome description",
            "vendor": "Avamagic",
            "model": "MGServer Client",
            }
        nonexist_oid = ObjectId()
        resp = self.client.put("/v1/devices/{}".format(str(nonexist_oid)),
                               data=data)

        self.assert_404(resp)

        resp = self.client.get("/v1/device")
        assert "success" == resp.json["flag"]
        device = resp.json["res"]
        assert old_timestamp == device["updated_since"]


class TestOAuth(TestCase):

    def test_unauthorized(self):
        response = self.client.get('/v1/devices')
        self.assert_400(response)


class TestExceptions(TestCaseWithoutAuth):

    def test_ApiException_default(self):
        e = ApiException()
        assert 500 == e.code
        assert "" == e.msg

    def test_ApiException_explicit(self):
        e = ApiException(401, "Unauthorized")
        assert 401 == e.code
        assert "Unauthorized" == e.msg


class TestUtils(TestCaseWithoutAuth):

    def test_epoch_field(self):
        DATETIME_UTC = datetime(2013, 2, 27, 15, 21, 53, 0, None)
        EPOCH = 1361978513

        obj = {"bar": DATETIME_UTC}
        field = Epoch()
        self.assertEquals(EPOCH, field.output("bar", obj))

    def test_epoch_invalid(self):
        obj = {"bar": "foo"}
        field = Epoch()
        with self.assertRaises(fields.MarshallingException):
            field.output("bar", obj)
