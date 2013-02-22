from werkzeug.urls import url_quote
from flask import url_for
from mgserver.extensions import provider
from mgserver.database import ResourceOwner as User
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

        new_user = User.find_one({'name': data['name']})
        assert new_user is not None

        self.assert_redirects(response, location=url_for('frontend.index'))

    def test_login(self):
        self._test_get_request('/login', 'login.html')


class TestApi(TestCase):

    def test_unauthorized(self):
        response = self.client.get('/v1/devices')
        self.assert_401(response)


class TestError(TestCase):

    def test_404(self):
        response = self.client.get('/404/')
        self.assert_404(response)
