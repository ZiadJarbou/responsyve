import base64
import hashlib
import json
import os
import unittest
import uuid
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from app import create_app, LeaseSigner

CODE = 'A' * 43  # Public test credential only; never a deployment credential.

class ReviewerAccess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        cls.signer = LeaseSigner(cls.pem)

    def client(self, **changes):
        env = {'REVIEWER_ACCESS_ENABLED':'true', 'REVIEWER_CREDENTIAL_SHA256':hashlib.sha256(CODE.encode()).hexdigest(), 'BILLING_ENABLED':'false', 'ENTITLEMENT_PRIVATE_KEY_B64':base64.b64encode(self.pem).decode()}
        env.update(changes)
        with patch.dict(os.environ, env, clear=True):
            return create_app(clock=lambda:1800000000).test_client()

    def body(self, **changes):
        body = dict(reviewCredential=CODE, installation=str(uuid.uuid4()), nonce=str(uuid.uuid4()))
        body.update(changes)
        return body

    def test_reusable_without_play_or_payment_and_short_separate_scope(self):
        client=self.client()
        for _ in range(2):
            body=self.body(); response=client.post('/v1/subscription/verify',json=body)
            self.assertEqual(response.status_code,200); self.assertTrue(response.json['active'])
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            claims=json.loads(base64.urlsafe_b64decode(response.json['lease'].split('.')[1]+'==='))
            self.assertEqual(claims,dict(aud='co.responsyve.tvremote',product='tv_remote_reviewer',sub=body['installation'],nonce=body['nonce'],iat=1800000000,exp=1800000600))

    def test_disabled_missing_malformed_or_rotated_secret_never_grants(self):
        for changes in [{'REVIEWER_ACCESS_ENABLED':'false'},{'REVIEWER_CREDENTIAL_SHA256':''},{'REVIEWER_CREDENTIAL_SHA256':'0'*64},{'ENTITLEMENT_PRIVATE_KEY_B64':'invalid'}]:
            with self.subTest(changes=list(changes)):
                self.assertEqual(self.client(**changes).post('/v1/subscription/verify',json=self.body()).json,{'active':False})

    def test_invalid_credentials_and_ids_fail_closed(self):
        for value in ['',None,[],CODE+'x','B'*43]:
            self.assertFalse(self.client().post('/v1/subscription/verify',json=self.body(reviewCredential=value)).json.get('active',False))
        for field in ['installation','nonce']:
            self.assertEqual(self.client().post('/v1/subscription/verify',json=self.body(**{field:'bad'})).status_code,400)

    def test_reviewer_cannot_unlock_normal_purchase_route(self):
        response=self.client().post('/v1/subscription/verify',json={'purchaseToken':CODE,'installation':str(uuid.uuid4()),'nonce':str(uuid.uuid4())})
        self.assertEqual(response.status_code,503);self.assertNotIn('lease',response.json)

    def test_auth_attempts_are_rate_limited(self):
        client=self.client()
        for _ in range(30):self.assertEqual(client.post('/v1/subscription/verify',json=self.body(reviewCredential='B'*43)).status_code,200)
        self.assertEqual(client.post('/v1/subscription/verify',json=self.body()).status_code,429)
