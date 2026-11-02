import base64
import json
import unittest
import uuid
from copy import deepcopy
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from app import create_app, LeaseSigner, entitlement_expiry, PRODUCT

NOW = 1800000000
PACKAGE = 'co.responsyve.tvremote'


def purchase(state='SUBSCRIPTION_STATE_ACTIVE', seconds=3600):
    return {'subscriptionState': state, 'acknowledgementState': 'ACKNOWLEDGEMENT_STATE_PENDING', 'lineItems': [{'productId': PRODUCT, 'offerDetails': {'basePlanId': 'monthly'}, 'expiryTime': datetime.fromtimestamp(NOW + seconds, timezone.utc).isoformat()}]}


class Publisher:
    def __init__(self, value): self.value, self.acknowledged = value, []
    def get(self, token): return deepcopy(self.value)
    def acknowledge(self, token): self.acknowledged.append(token)


class Entitlements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.signer = LeaseSigner(cls.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))

    def client(self, value):
        self.provider = Publisher(value)
        return create_app(self.provider, self.signer, PACKAGE, lambda: NOW).test_client()

    def body(self): return {'purchaseToken': 'test-only-token', 'installation': str(uuid.uuid4()), 'nonce': str(uuid.uuid4())}

    def test_active_signed_scoped_lease_and_ack(self):
        client, body = self.client(purchase()), self.body()
        response = client.post('/v1/subscription/verify', json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertTrue(response.json['active'])
        head, payload, signature = response.json['lease'].split('.')
        self.key.public_key().verify(base64.urlsafe_b64decode(signature+'==='), (head+'.'+payload).encode(), padding.PKCS1v15(), hashes.SHA256())
        claims = json.loads(base64.urlsafe_b64decode(payload+'==='))
        self.assertEqual(claims, {'aud': PACKAGE, 'product': PRODUCT, 'sub': body['installation'], 'nonce': body['nonce'], 'iat': NOW, 'exp': NOW+3600})
        self.assertEqual(self.provider.acknowledged, ['test-only-token'])

    def test_annual_purchase_grants_bounded_lease_and_acknowledges(self):
        value = purchase(seconds=365*86400)
        value['lineItems'][0]['offerDetails']['basePlanId'] = 'annual'
        response = self.client(value).post('/v1/subscription/verify', json=self.body())
        self.assertTrue(response.json['active'])
        claims = json.loads(base64.urlsafe_b64decode(response.json['lease'].split('.')[1]+'==='))
        self.assertEqual(claims['exp'], NOW+86400)
        self.assertEqual(self.provider.acknowledged, ['test-only-token'])

    def test_lease_never_exceeds_one_day(self):
        response = self.client(purchase(seconds=30*86400)).post('/v1/subscription/verify', json=self.body())
        claims = json.loads(base64.urlsafe_b64decode(response.json['lease'].split('.')[1]+'==='))
        self.assertEqual(claims['exp'], NOW+86400)

    def test_canceled_future_and_grace_remain_entitled(self):
        for state in ['SUBSCRIPTION_STATE_CANCELED', 'SUBSCRIPTION_STATE_IN_GRACE_PERIOD']:
            with self.subTest(state=state): self.assertTrue(self.client(purchase(state)).post('/v1/subscription/verify', json=self.body()).json['active'])

    def test_pending_paused_hold_expired_unknown_never_unlock(self):
        for state in ['SUBSCRIPTION_STATE_PENDING', 'SUBSCRIPTION_STATE_PAUSED', 'SUBSCRIPTION_STATE_ON_HOLD', 'SUBSCRIPTION_STATE_EXPIRED', '', 'SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED']:
            with self.subTest(state=state):
                response = self.client(purchase(state)).post('/v1/subscription/verify', json=self.body())
                self.assertEqual(response.json, {'active': False})
                self.assertEqual(self.provider.acknowledged, [])

    def test_expired_active_and_wrong_product_or_plan_fail(self):
        cases = [purchase(seconds=0), purchase(seconds=-10), purchase()]
        cases[2]['lineItems'][0]['productId'] = 'wrong'
        wrong_plan = purchase(); wrong_plan['lineItems'][0]['offerDetails']['basePlanId'] = 'unknown'; cases.append(wrong_plan)
        malformed = purchase(); malformed['lineItems'][0]['expiryTime'] = 'broken'; cases.append(malformed)
        for value in cases:
            with self.subTest(value=value): self.assertIsNone(entitlement_expiry(value, NOW))

    def test_already_acknowledged_not_reacknowledged(self):
        value = purchase(); value['acknowledgementState'] = 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'
        response = self.client(value).post('/v1/subscription/verify', json=self.body())
        self.assertTrue(response.json['active']); self.assertEqual(self.provider.acknowledged, [])

    def test_missing_ack_state_denies(self):
        value = purchase(); value.pop('acknowledgementState')
        self.assertFalse(self.client(value).post('/v1/subscription/verify', json=self.body()).json['active'])

    def test_invalid_requests_and_body_limits(self):
        client = self.client(purchase())
        for body in [{}, {'purchaseToken': 'x'}, [], self.body() | {'installation': 'bad'}, self.body() | {'purchaseToken': 'a\nb'}]:
            with self.subTest(body=body): self.assertEqual(client.post('/v1/subscription/verify', json=body).status_code, 400)
        self.assertEqual(client.post('/v1/subscription/verify', data='x'*9000, content_type='application/json').status_code, 413)

    def test_upstream_or_ack_failure_never_grants(self):
        client = self.client(purchase())
        def fail(_): raise RuntimeError('private upstream data')
        self.provider.acknowledge = fail
        response = client.post('/v1/subscription/verify', json=self.body())
        self.assertEqual(response.status_code, 503); self.assertNotIn('private', response.get_data(as_text=True))
        self.provider.get = fail
        self.assertEqual(client.post('/v1/subscription/verify', json=self.body()).status_code, 503)


if __name__ == '__main__': unittest.main()
