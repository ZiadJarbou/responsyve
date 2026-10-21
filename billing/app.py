"""Stateless Play verification. Never accept a client price, expiry, or active flag."""
import base64
import json
import os
import time
import uuid
import threading
import hashlib
import hmac
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

PRODUCT = 'tv_remote_access'
BASE_PLAN = 'monthly'
ACTIVE_STATES = {'SUBSCRIPTION_STATE_ACTIVE', 'SUBSCRIPTION_STATE_IN_GRACE_PERIOD', 'SUBSCRIPTION_STATE_CANCELED'}


def entitlement_expiry(purchase, now):
    if purchase.get('subscriptionState') not in ACTIVE_STATES:
        return None
    expiries = []
    for item in purchase.get('lineItems', []):
        if item.get('productId') != PRODUCT or item.get('offerDetails', {}).get('basePlanId') != BASE_PLAN:
            continue
        try:
            expires = int(datetime.fromisoformat(item['expiryTime'].replace('Z', '+00:00')).timestamp())
        except (KeyError, ValueError, TypeError):
            continue
        if expires > now:
            expiries.append(expires)
    return max(expiries) if expiries else None


def b64(value):
    return base64.urlsafe_b64encode(value).decode('ascii').rstrip('=')


class LeaseSigner:
    def __init__(self, pem):
        self.key = serialization.load_pem_private_key(pem, password=None)
        if not isinstance(self.key, rsa.RSAPrivateKey) or self.key.key_size < 2048:
            raise ValueError('RSA 2048-bit or stronger signing key required')

    def sign(self, claims):
        header = b64(b'{"alg":"RS256","typ":"JWT"}')
        payload = b64(json.dumps(claims, separators=(',', ':'), sort_keys=True).encode())
        signing_input = (header + '.' + payload).encode('ascii')
        signature = self.key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        return signing_input.decode() + '.' + b64(signature)


class PlayPublisher:
    def __init__(self, package):
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        encoded = os.environ.get('GOOGLE_SERVICE_ACCOUNT_B64')
        if encoded:
            from google.oauth2 import service_account
            info = json.loads(base64.b64decode(encoded, validate=True))
            if info.get('type') != 'service_account' or info.get('token_uri') != 'https://oauth2.googleapis.com/token':
                raise ValueError('Expected Google service account credentials')
            credentials = service_account.Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/androidpublisher'])
        else:
            credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/androidpublisher'])
        self.session = AuthorizedSession(credentials)
        self.package = package

    def get(self, token):
        url = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/' + quote(self.package, safe='') + '/purchases/subscriptionsv2/tokens/' + quote(token, safe='')
        response = self.session.get(url, timeout=15)
        if response.status_code in (400, 404, 410):
            return {}
        if response.status_code != 200:
            raise RuntimeError('Play verification unavailable')
        return response.json()

    def acknowledge(self, token):
        url = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/' + quote(self.package, safe='') + '/purchases/subscriptions/' + PRODUCT + '/tokens/' + quote(token, safe='') + ':acknowledge'
        response = self.session.post(url, json={}, timeout=15)
        if response.status_code not in (200, 204):
            # Another retry/process may already have acknowledged the same purchase.
            if self.get(token).get('acknowledgementState') != 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED':
                raise RuntimeError('Play acknowledgement unavailable')


def helper_configuration():
    url = os.environ.get('PLAY_HELPER_URL', '')
    secret = os.environ.get('PLAY_HELPER_SHARED_SECRET', '')
    try:
        parsed = urlparse(url)
        valid = (parsed.scheme == 'https' and parsed.hostname and parsed.hostname.endswith('.run.app')
             and parsed.path == '/internal/play/verify' and not parsed.query and not parsed.fragment
             and not parsed.username and not parsed.password and parsed.port in (None, 443)
             and len(secret) >= 43 and not any(c.isspace() for c in secret))
    except ValueError:
        valid = False
    return url, secret, bool(valid)


class RemotePlayPublisher:
    """Only the configured Cloud Run helper may attest to Google purchase state."""
    def __init__(self):
        self.url, self.secret, valid = helper_configuration()
        if not valid: raise ValueError('Invalid helper configuration')

    def get(self, token):
        import requests
        with requests.post(self.url, json={'purchaseToken': token},
                           headers={'Authorization': 'Bearer ' + self.secret}, timeout=(5, 30),
                           allow_redirects=False, stream=True) as response:
            if response.status_code != 200: raise RuntimeError('Play helper unavailable')
            body = bytearray()
            for chunk in response.iter_content(4096):
                body.extend(chunk)
                if len(body) > 16384: raise RuntimeError('Play helper response too large')
            purchase = json.loads(body).get('purchase')
        if not isinstance(purchase, dict): raise RuntimeError('Invalid helper response')
        return purchase

    def acknowledge(self, token):
        # The helper acknowledges a valid purchase before returning it.
        raise RuntimeError('Unexpected unacknowledged helper response')


def signing_key_base64():
    full = os.environ.get('ENTITLEMENT_PRIVATE_KEY_B64')
    if full:
        return full
    parts = []
    for i in range(1, 5):
        canonical = os.environ.get('ENTITLEMENT_PRIVATE_KEY_B64_' + str(i), '')
        saved_name = os.environ.get('ENTITLEMENT_PRIVATE_KEY_B64' + str(i), '')
        if canonical and saved_name and canonical != saved_name:
            raise ValueError('Conflicting signing key configuration')
        parts.append(canonical or saved_name)
    return ''.join(parts)


def create_app(publisher=None, signer=None, package=None, clock=time.time):
    injected = publisher is not None and signer is not None
    package = package or os.environ.get('PLAY_PACKAGE_NAME', 'co.responsyve.tvremote')
    enabled = injected or os.environ.get('BILLING_ENABLED') == 'true'
    configuration_ok = False
    reviewer_enabled = os.environ.get('REVIEWER_ACCESS_ENABLED') == 'true'
    reviewer_hash = os.environ.get('REVIEWER_CREDENTIAL_SHA256', '')
    if not re.fullmatch('[0-9a-f]{64}', reviewer_hash):
        reviewer_enabled = False
    if not signer and (enabled or reviewer_enabled):
        try:
            encoded = signing_key_base64()
            pem = base64.b64decode(encoded, validate=True) if encoded else Path(os.environ['ENTITLEMENT_PRIVATE_KEY_FILE']).read_bytes()
            signer = LeaseSigner(pem)
        except Exception:
            # Do not expose credentials or configuration values in startup errors.
            signer = None
    helper_url, _, helper_valid = helper_configuration()
    google_configured = helper_valid if helper_url else bool(os.environ.get('GOOGLE_SERVICE_ACCOUNT_B64') or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
    configuration_ok = enabled and signer is not None and (injected or google_configured)
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 8192
    recent = deque()
    review_recent = deque()
    guard = threading.Lock()
    # A global ceiling bounds upstream API cost on a small single-worker deployment.
    concurrent = threading.BoundedSemaphore(2)

    def play():
        nonlocal publisher
        if publisher is None:
            publisher = RemotePlayPublisher() if helper_url else PlayPublisher(package)
        return publisher

    @app.after_request
    def private_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/health')
    def health():
        return jsonify(status='ok', billing_configured=configuration_ok)

    @app.get('/ready')
    def ready():
        # Configuration readiness does not prove Play Console permissions or purchases.
        return jsonify(configured=configuration_ok), 200 if configuration_ok else 503

    @app.post('/v1/subscription/verify')
    def verify():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error='Invalid request'), 400
        if 'reviewCredential' in data:
            # Separate grant type; never synthesize a purchase or consult Play.
            with guard:
                tick = time.monotonic()
                while review_recent and review_recent[0] <= tick - 60:
                    review_recent.popleft()
                if len(review_recent) >= 30:
                    return jsonify(error='Please retry shortly'), 429
                review_recent.append(tick)
            try:
                uuid.UUID(data.get('installation'))
                uuid.UUID(data.get('nonce'))
            except (ValueError, TypeError, AttributeError):
                return jsonify(error='Invalid request'), 400
            credential = data.get('reviewCredential')
            if not isinstance(credential, str) or not re.fullmatch('[A-Za-z0-9_-]{43}', credential):
                return jsonify(active=False)
            if not reviewer_enabled or signer is None:
                return jsonify(active=False)
            digest = hashlib.sha256(credential.encode('ascii')).hexdigest()
            if not hmac.compare_digest(digest, reviewer_hash):
                return jsonify(active=False)
            now = int(clock())
            claims = {'aud': package, 'product': 'tv_remote_reviewer', 'sub': data['installation'],
                      'nonce': data['nonce'], 'iat': now, 'exp': now + 600}
            try:
                return jsonify(active=True, lease=signer.sign(claims))
            except Exception:
                return jsonify(error='Reviewer verification temporarily unavailable'), 503
        token, installation, nonce = (data.get(k) for k in ('purchaseToken', 'installation', 'nonce'))
        if not isinstance(token, str) or not 1 <= len(token) <= 4096 or any(c.isspace() or ord(c) < 32 for c in token):
            return jsonify(error='Invalid request'), 400
        try:
            uuid.UUID(installation)
            uuid.UUID(nonce)
        except (ValueError, TypeError, AttributeError):
            return jsonify(error='Invalid request'), 400
        if not configuration_ok:
            return jsonify(error='Subscription verification is not enabled'), 503
        with guard:
            now_tick = time.monotonic()
            while recent and recent[0] <= now_tick - 60:
                recent.popleft()
            if len(recent) >= 60:
                return jsonify(error='Please retry shortly'), 429
            recent.append(now_tick)
        if not concurrent.acquire(blocking=False):
            return jsonify(error='Please retry shortly'), 429
        try:
            purchase = play().get(token)
            now = int(clock())
            expiry = entitlement_expiry(purchase, now)
            if expiry is None:
                return jsonify(active=False)
            acknowledgement = purchase.get('acknowledgementState')
            if acknowledgement == 'ACKNOWLEDGEMENT_STATE_PENDING':
                play().acknowledge(token)
            elif acknowledgement != 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED':
                return jsonify(active=False)
            claims = {'aud': package, 'product': PRODUCT, 'sub': installation, 'nonce': nonce, 'iat': now, 'exp': min(expiry, now + 86400)}
            return jsonify(active=True, lease=signer.sign(claims))
        except Exception:
            # Tokens, signed leases, credentials, and upstream URLs must never reach logs.
            return jsonify(error='Subscription verification temporarily unavailable'), 503
        finally:
            concurrent.release()

    return app
