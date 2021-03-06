from flask import request, render_template, g, url_for, redirect
from flask.ext.oauthprovider import OAuthProvider
from flask.ext.login import current_user
from bson.objectid import ObjectId
from .helper import get_or_create_device
from .models import ResourceOwner as User, Client, Nonce
from .models import RequestToken, AccessToken


class MongoProvider(OAuthProvider):

    @property
    def request_token_url(self):
        return u'/v1/request_token'

    @property
    def access_token_url(self):
        return u'/v1/access_token'

    @property
    def register_url(self):
        return u'/v1/register'

    @property
    def authorize_url(self):
        return u'/v1/authorize'

    @property
    def enforce_ssl(self):
        return False

    @property
    def realms(self):
        return [u"users", u"vendors", u"admins"]

    @property
    def nonce_length(self):
        return 20, 40

    def authorize(self):
        # HACK: authorize directly if uid is provided and not password protected
        uid = request.values.get('uid')
        user = User.find_one({"_id": ObjectId(uid)}) if uid else None
        if (user is not None and user["email"] == "" and user["pw_hash"] == ""):
            g.hack_user = user
            token = request.values.get("oauth_token")
            return self.authorized(token)

        # Check logged in
        if not current_user.is_authenticated():
            next_url = url_for("frontend.login") + "?next=" + request.url
            return redirect(next_url)

        if request.method == "POST":
            token = request.form.get("oauth_token")
            return self.authorized(token)
        else:
            token = request.args.get("oauth_token")
            try:
                requestToken = RequestToken.find_one({"token": token})
                client = Client.find_one({"_id": requestToken["client_id"]})
                client_name = client["name"]
            except:
                client_name = ""

            return render_template("authorize.html",
                                   token=token,
                                   client_name=client_name)

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
            request_token=None, access_token=None):

        token = True
        req_token = True
        client = Client.find_one({'client_key':client_key})

        if client:
            nonce = Nonce.find_one({'nonce':nonce, 'timestamp':timestamp,
                'client_id':client['_id']})

            if nonce:
                if request_token:
                    req_token = RequestToken.find_one(
                        {'_id':nonce['request_token_id'], 'token':request_token})

                if access_token:
                    token = RequestToken.find_one(
                        {'_id':nonce['request_token_id'], 'token':access_token})

        return token and req_token and nonce != None

    def validate_redirect_uri(self, client_key, redirect_uri=None):
        client = Client.find_one({'client_key':client_key})

        return client != None and (
            len(client['callbacks']) == 1 and redirect_uri is None
            or redirect_uri in (x for x in client['callbacks']))


    def validate_client_key(self, client_key):
        return (
            Client.find_one({'client_key':client_key}) != None)


    def validate_requested_realm(self, client_key, realm):
        return True


    def validate_realm(self, client_key, access_token, uri=None, required_realm=None):

        if not required_realm:
            return True

        # insert other check, ie on uri here

        client = Client.find_one({'client_key':client_key})

        if client:
            token = AccessToken.find_one(
                {'token':access_token, 'client_id': client['_id']})

            if token:
                return token['realm'] in required_realm

        return False

    @property
    def dummy_client(self):
        return u'dummy_client'

    @property
    def dummy_resource_owner(self):
        return u'dummy_resource_owner'

    def validate_request_token(self, client_key, resource_owner_key):
        # TODO: make client_key optional
        token = None

        if client_key:
            client = Client.find_one({'client_key':client_key})

            if client:
                token = RequestToken.find_one(
                    {'token':access_token, 'client_id': client['_id']})

        else:
            token = RequestToken.find_one(
                    {'token':resource_owner_key})

        return token != None


    def validate_access_token(self, client_key, resource_owner_key):

        token = None
        client = Client.find_one({'client_key':client_key})

        if client:
            token = AccessToken.find_one(
                {'token':resource_owner_key, 'client_id': client['_id']})

        return token != None


    def validate_verifier(self, client_key, resource_owner_key, verifier):
        token = None
        client = Client.find_one({'client_key':client_key})

        if client:
            token = RequestToken.find_one(
                {'token':resource_owner_key,
                 'client_id': client['_id'],
                 'verifier':verifier})

        return token != None


    def get_callback(self, request_token):
        token = RequestToken.find_one(
                {'token':request_token})

        if token:
            return token.get('callback')
        else:
            return None


    def get_realm(self, client_key, request_token):
        client = Client.find_one({'client_key':client_key})

        if client:
            token = RequestToken.find_one(
                {'token':request_token, 'client_id': client['_id']})

            if token:
                return token.get('realm')

        return None


    def get_client_secret(self, client_key):
            client = Client.find_one({'client_key':client_key})

            if client:
                return client.get('secret')
            else:
                return None


    def get_rsa_key(self, client_key):
            client = Client.find_one({'client_key':client_key})

            if client:
                return client.get('pubkey')
            else:
                return None

    def get_request_token_secret(self, client_key, resource_owner_key):
        client = Client.find_one({'client_key':client_key})

        if client:
            token = RequestToken.find_one(
                {'token':resource_owner_key,
                 'client_id': client['_id']})

            if token:
                return token.get('secret')

        return None


    def get_access_token_secret(self, client_key, resource_owner_key):
        client = Client.find_one({'client_key':client_key})

        if client:
            token = AccessToken.find_one(
                {'token':resource_owner_key,
                 'client_id': client['_id']})

            if token:
                return token.get('secret')

        return None

    def save_request_token(self, client_key, request_token, callback,
            realm=None, secret=None):
        client = Client.find_one({'client_key':client_key})

        if client:
            token = RequestToken(
                request_token, callback, secret=secret, realm=realm)
            token.client_id = client['_id']

            RequestToken.insert(token)

    def save_access_token(self, client_key, access_token, request_token,
            realm=None, secret=None):
        client = Client.find_one({'client_key':client_key})

        if client:
            token = AccessToken(access_token, secret=secret, realm=realm)
            token.client_id = client['_id']

            req_token = RequestToken.find_one({'token':request_token})

            if req_token:
                token['resource_owner_id'] = req_token['resource_owner_id']
                token['realm'] = req_token['realm']

                AccessToken.insert(token)

                # make sure device exist
                device = get_or_create_device(token)

    def save_timestamp_and_nonce(self, client_key, timestamp, nonce,
            request_token=None, access_token=None):

        client = Client.find_one({'client_key':client_key})

        if client:
            nonce = Nonce(nonce, timestamp)
            nonce.client_id = client['_id']

            if request_token:
                req_token = RequestToken.find_one({'token':request_token})
                nonce.request_token_id = req_token['_id']

            if access_token:
                token = AccessToken.find_one({'token':access_token})
                nonce.access_token_id = token['_id']

            Nonce.insert(nonce)

    def save_verifier(self, request_token, verifier):
        token = RequestToken.find_one({'token': request_token})
        token['verifier'] = verifier
        if hasattr(g, 'hack_user'):
            user, g.hack_user = g.hack_user, None
        else:
            user = current_user
        token['resource_owner_id'] = user['_id']
        RequestToken.get_collection().save(token)
