from werkzeug.urls import url_quote
from flask import url_for
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


class TestApi(TestCase):

    def test_unauthorized(self):
        response = self.client.get('/v1/devices')
        self.assert_400(response)

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


class TestError(TestCase):

    def test_404(self):
        response = self.client.get('/404/')
        self.assert_404(response)
