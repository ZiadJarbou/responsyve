import os
import unittest
from unittest.mock import patch
from cloud_run_helper import create_app
import test_entitlements as fixtures

SECRET = 'synthetic-test-secret-only-not-production-0000000000'


class KeylessHelper(unittest.TestCase):
    def client(self, value=None, enabled=True):
        self.publisher = fixtures.Publisher(value if value is not None else fixtures.purchase())
        return create_app(self.publisher, lambda: fixtures.NOW, SECRET, enabled).test_client()

    def post(self, client, body=None, secret=SECRET):
        return client.post('/internal/play/verify', json=body if body is not None else {'purchaseToken': 'test-token'}, headers={'Authorization': 'Bearer ' + secret})

    def test_no_or_wrong_gateway_credential_never_calls_google(self):
        client = self.client()
        for secret in ['', 'wrong']:
            self.assertEqual(self.post(client, secret=secret).status_code, 401)
        self.assertEqual(self.publisher.acknowledged, [])

    def test_valid_purchase_acknowledged_and_sanitized(self):
        value = fixtures.purchase(); value['latestOrderId'] = 'private-order'; value['externalAccountIdentifiers'] = {'email': 'private'}
        response = self.post(self.client(value))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['purchase']['acknowledgementState'], 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED')
        self.assertEqual(self.publisher.acknowledged, ['test-token'])
        self.assertNotIn('private', response.text)
        self.assertNotIn('lease', response.json)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_annual_plan_is_preserved_in_sanitized_result(self):
        value = fixtures.purchase(seconds=365*86400)
        value['lineItems'][0]['offerDetails']['basePlanId'] = 'annual'
        response = self.post(self.client(value))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['purchase']['lineItems'][0]['offerDetails']['basePlanId'], 'annual')
        self.assertEqual(self.publisher.acknowledged, ['test-token'])

    def test_inactive_wrong_plan_and_expired_never_acknowledged(self):
        wrong = fixtures.purchase(); wrong['lineItems'][0]['offerDetails']['basePlanId'] = 'wrong'
        for value in [fixtures.purchase('SUBSCRIPTION_STATE_ON_HOLD'), fixtures.purchase(seconds=-1), wrong]:
            response = self.post(self.client(value))
            self.assertEqual(response.json, {'purchase': {}})
            self.assertEqual(self.publisher.acknowledged, [])

    def test_disabled_checks_do_not_call_google(self):
        response = self.post(self.client(enabled=False))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.publisher.acknowledged, [])

    def test_invalid_and_oversized_requests(self):
        client = self.client()
        for body in [{}, {'purchaseToken': 'bad token'}, {'purchaseToken': 5}]:
            self.assertEqual(self.post(client, body).status_code, 400)
        self.assertEqual(self.post(client, {'purchaseToken': 'x'*9000}).status_code, 413)

    def test_downloaded_credentials_rejected_in_keyless_environment(self):
        with patch.dict(os.environ, {'K_SERVICE': 'test', 'GOOGLE_APPLICATION_CREDENTIALS': '/not-a-real-file', 'PLAY_HELPER_SHARED_SECRET': SECRET, 'PLAY_CHECKS_ENABLED': 'true'}, clear=True):
            app = create_app()
            self.assertFalse(app.test_client().get('/health').json['google_checks_configured'])

    def test_ack_failure_never_returns_verified_purchase(self):
        client = self.client()
        def fail(token): raise RuntimeError('private-upstream-error')
        self.publisher.acknowledge = fail
        response = self.post(client)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', response.text)


if __name__ == '__main__': unittest.main()
