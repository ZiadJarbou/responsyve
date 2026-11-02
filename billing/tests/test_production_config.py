import os
import unittest
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from app import create_app
import test_entitlements as fixtures


class ProductionConfiguration(unittest.TestCase):
    def test_disabled_server_boots_and_never_grants(self):
        with patch.dict(os.environ, {}, clear=True):
            client = create_app().test_client()
            self.assertEqual(client.get('/health').json, {'status': 'ok', 'billing_configured': False})
            self.assertEqual(client.get('/ready').status_code, 503)
            response = client.post('/v1/subscription/verify', json={'purchaseToken': 'synthetic', 'installation': '123e4567-e89b-12d3-a456-426614174000', 'nonce': '123e4567-e89b-12d3-a456-426614174001'})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('lease', response.json)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_bad_key_fails_closed_without_leaking_value(self):
        with patch.dict(os.environ, {'BILLING_ENABLED': 'true', 'ENTITLEMENT_PRIVATE_KEY_B64': 'private-invalid-value'}, clear=True):
            response = create_app().test_client().get('/ready')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private-invalid-value', response.text)

    def test_large_requests_are_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            response = create_app().test_client().post('/v1/subscription/verify', data=b'x' * 9000, content_type='application/json')
            self.assertEqual(response.status_code, 413)

    def test_global_rate_ceiling(self):
        fixtures.Entitlements.setUpClass()
        client = create_app(fixtures.Publisher({}), fixtures.Entitlements.signer, fixtures.PACKAGE).test_client()
        body = {'purchaseToken': 'synthetic', 'installation': '123e4567-e89b-12d3-a456-426614174000', 'nonce': '123e4567-e89b-12d3-a456-426614174001'}
        for _ in range(60): self.assertEqual(client.post('/v1/subscription/verify', json=body).status_code, 200)
        self.assertEqual(client.post('/v1/subscription/verify', json=body).status_code, 429)

    def test_concurrency_ceiling(self):
        fixtures.Entitlements.setUpClass()
        entered, release = queue.Queue(), threading.Event()
        class SlowPublisher:
            def get(self, token):
                entered.put(True)
                if not release.wait(5): raise RuntimeError('test timeout')
                return {}
        app = create_app(SlowPublisher(), fixtures.Entitlements.signer, fixtures.PACKAGE)
        body = {'purchaseToken': 'synthetic', 'installation': '123e4567-e89b-12d3-a456-426614174000', 'nonce': '123e4567-e89b-12d3-a456-426614174001'}
        def post(): return app.test_client().post('/v1/subscription/verify', json=body).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(post) for _ in range(2)]
            try:
                entered.get(timeout=3); entered.get(timeout=3)
                self.assertEqual(post(), 429)
            finally: release.set()
            self.assertEqual([f.result(timeout=3) for f in futures], [200, 200])


if __name__ == '__main__': unittest.main()
