import json
import os
import unittest
from unittest.mock import patch
from app import RemotePlayPublisher, helper_configuration, create_app
import test_entitlements as fixtures
from cloud_run_helper import create_app as helper_app

SECRET = 'synthetic-test-secret-only-not-production-0000000000'
URL = 'https://synthetic-helper.run.app/internal/play/verify'


class Reply:
    def __init__(self, status, body): self.status_code, self.body = status, body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def iter_content(self, size):
        for offset in range(0, len(self.body), size): yield self.body[offset:offset+size]


class RemoteHelper(unittest.TestCase):
    def test_only_expected_https_helper_route_is_valid(self):
        for url in ['http://helper.run.app/internal/play/verify','https://evil.example/internal/play/verify','https://helper.run.app/other','https://user:pass@helper.run.app/internal/play/verify','https://helper.run.app/internal/play/verify?token=x','https://[bad']:
            with patch.dict(os.environ, {'PLAY_HELPER_URL':url,'PLAY_HELPER_SHARED_SECRET':SECRET}, clear=True):
                self.assertFalse(helper_configuration()[2])
        with patch.dict(os.environ, {'PLAY_HELPER_URL':URL,'PLAY_HELPER_SHARED_SECRET':SECRET}, clear=True):
            self.assertTrue(helper_configuration()[2])

    def test_helper_to_spaceship_signed_lease_path(self):
        fixtures.Entitlements.setUpClass()
        provider = fixtures.Publisher(fixtures.purchase())
        helper = helper_app(provider, lambda: fixtures.NOW, SECRET, True, 'all-purchases').test_client()
        def exchange(url, **kwargs):
            self.assertEqual(url,URL);self.assertFalse(kwargs['allow_redirects']);self.assertTrue(kwargs['stream'])
            reply=helper.post('/internal/play/verify',json=kwargs['json'],headers=kwargs['headers'])
            return Reply(reply.status_code,reply.data)
        with patch.dict(os.environ, {'PLAY_HELPER_URL':URL,'PLAY_HELPER_SHARED_SECRET':SECRET}, clear=True), patch('requests.post',side_effect=exchange):
            client=create_app(RemotePlayPublisher(),fixtures.Entitlements.signer,fixtures.PACKAGE,lambda:fixtures.NOW).test_client()
            reply=client.post('/v1/subscription/verify',json={'purchaseToken':'synthetic','installation':'123e4567-e89b-12d3-a456-426614174000','nonce':'123e4567-e89b-12d3-a456-426614174001'})
            self.assertEqual(reply.status_code,200);self.assertTrue(reply.json['active']);self.assertIn('lease',reply.json)
            self.assertEqual(provider.acknowledged,['synthetic'])

    def test_auth_denial_redirect_and_large_reply_fail_closed(self):
        with patch.dict(os.environ, {'PLAY_HELPER_URL':URL,'PLAY_HELPER_SHARED_SECRET':SECRET}, clear=True):
            for reply in [Reply(401,b'{}'),Reply(302,b'{}'),Reply(200,b'x'*16385),Reply(200,b'not-json')]:
                with patch('requests.post',return_value=reply), self.assertRaises(Exception): RemotePlayPublisher().get('synthetic')

    def test_default_test_only_helper_prevents_real_purchase_access_grant(self):
        fixtures.Entitlements.setUpClass()
        provider = fixtures.Publisher(fixtures.purchase())
        with patch.dict(os.environ, {}, clear=True):
            helper = helper_app(provider, lambda: fixtures.NOW, SECRET, True).test_client()
        def exchange(url, **kwargs):
            reply = helper.post('/internal/play/verify', json=kwargs['json'], headers=kwargs['headers'])
            return Reply(reply.status_code, reply.data)
        with patch.dict(os.environ, {'PLAY_HELPER_URL':URL,'PLAY_HELPER_SHARED_SECRET':SECRET}, clear=True), patch('requests.post',side_effect=exchange):
            client = create_app(RemotePlayPublisher(),fixtures.Entitlements.signer,fixtures.PACKAGE,lambda:fixtures.NOW).test_client()
            reply = client.post('/v1/subscription/verify',json={'purchaseToken':'synthetic','installation':'123e4567-e89b-12d3-a456-426614174000','nonce':'123e4567-e89b-12d3-a456-426614174001'})
            self.assertFalse(reply.json['active'])
            self.assertNotIn('lease', reply.json)
            self.assertEqual(provider.acknowledged, [])


if __name__ == '__main__': unittest.main()
