from werkzeug.urls import url_quote
from bson.objectid import ObjectId
from flask import url_for
from mgserver.common import ApiException
from mgserver.extensions import provider, totp
from mgserver.database import ResourceOwner as User, Client
from tests import TestCase


class TestFrontend(TestCase):

    def test_show(self):
        self._test_get_request('/', 'index.html')

    def test_index_authenticated(self):
        self.login("known_user@example.com", "9527")

        response = self.client.get('/')
        self.assert_redirects(response, location=url_for('frontend.devices'))

        response = self.client.get('/', follow_redirects=True)
        self.assert_template_used(name='devices.html')

    def test_account(self):
        self.login("known_user@example.com", "9527")
        response = self.client.get("/account")
        self.assert_template_used(name="account.html")

    def test_add_app(self):
        self.login("known_user@example.com", "9527")

        data = {
            u"name": "Fake app",
            u"description": "Official fake app for MGServer",
            u"callback": "xxx://yyy.zzz",
            }
        response = self.client.post('/apps', data=data)

        app = Client.find_one({u"name": data["name"]})
        assert app is not None

        self.assert_redirects(response, location=url_for("frontend.apps"))

    def test_add_app_empty_name(self):
        self.login("known_user@example.com", "9527")

        data = {
            u"name": "",
            u"description": "Official fake app for MGServer",
            u"callback": "xxx://yyy.zzz",
            }
        response = self.client.post('/apps', data=data)

        app = Client.find_one({u"name": data["name"]})
        assert app is None

    def test_add_app_invalid_callback(self):
        self.login("known_user@example.com", "9527")

        data = {
            u"name": "Fake app",
            u"description": "Official fake app for MGServer",
            u"callback": "xxx:/yyy.zzz",
            }
        response = self.client.post('/apps', data=data)

        app = Client.find_one({u"name": data["name"]})
        assert app is None

    def test_add_duplicated_app(self):
        self.login("known_user@example.com", "9527")

        data = {
            u"name": "Fake app",
            u"description": "Official fake app for MGServer",
            u"callback": "xxx://yyy.zzz",
            }
        response = self.client.post('/apps', data=data)
        response = self.client.post('/apps', data=data, follow_redirects=True)

        assert "already exist" in response.data

    def test_signup(self):
        self._test_get_request('/signup', 'signup.html')

        data = {
            'name': 'New User',
            'email': 'new_user@example.com',
            'password': '123456',
            'confirm': '123456',
        }
        response = self.client.post('/signup', data=data)
        assert "control-group error" not in response.data

        new_user = User.find_one({'email': data['email']})
        assert new_user is not None

        self.assert_redirects(response, location=url_for('frontend.index'))

    def test_duplicate_signup(self):
        data = {
            'name': 'New User',
            'email': 'new_user@example.com',
            'password': '123456',
            'confirm': '123456',
            }
        response = self.client.post('/signup', data=data, follow_redirects=True)
        count = User.find({'name': data['name']}).count()
        assert count == 1

        self._logout()

        response = self.client.post('/signup', data=data, follow_redirects=True)
        count = User.find({'name': data['name']}).count()
        assert count == 1

        assert "This email address is already signed up" in response.data

    def test_signup_authenticated(self):
        self.login("known_user@example.com", "9527")
        data = {
            'name': 'New User',
            'email': 'new_user@example.com',
            'password': '123456',
            'confirm': '123456',
            }
        response = self.client.post('/signup', data=data)
        self.assert_redirects(response, location=url_for("frontend.index"))

    def test_login(self):
        self._test_get_request('/login', 'login.html')

    def test_login_success(self):
        response = self.login("known_user@example.com", "9527")
        assert "Signed in successfully." in response.data

    def test_login_fail(self):
        response = self.login("unknown_user@example.com", "123456")
        assert "Invalid credentials" in response.data
        self.assert_template_used(name="login.html")

    def test_already_login(self):
        self.login("known_user@example.com", "9527")
        response = self.login("known_user@example.com", "9527", follow_redirects=False)
        self.assert_redirects(response, location=url_for("frontend.index"))

    def test_logout(self):
        self.login("known_user@example.com", "9527")
        response = self.client.get('/')
        self.assert_redirects(response, location=url_for('frontend.devices'))

        self._logout()
        response = self.client.get('/')
        self.assert_template_used(name="index.html")


class TestOAuth(TestCase):

    def test_unauthorized(self):
        response = self.client.get('/v1/devices')
        self.assert_400(response)


class TestApi(TestCase):

    def setUp(self):
        super(TestApi, self).setUp()

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

    def test_ApiException_default(self):
        e = ApiException()
        assert 500 == e.code
        assert "" == e.msg

    def test_ApiException_explicit(self):
        e = ApiException(401, "Unauthorized")
        assert 401 == e.code
        assert "Unauthorized" == e.msg


class TestError(TestCase):

    def test_404(self):
        response = self.client.get('/404/')
        self.assert_404(response)
