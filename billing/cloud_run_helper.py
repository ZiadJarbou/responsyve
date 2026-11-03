"""Keyless Google Play lookup/acknowledgement only. No lease-signing key is held here."""
import hmac
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from app import PlayPublisher, entitlement_details, PRODUCT


def create_app(publisher=None, clock=time.time, shared_secret=None, checks_enabled=None, purchase_mode=None):
    # Explicit attached-identity mode. Never accept downloadable Google credentials here.
    keyless_environment = bool(os.environ.get('K_SERVICE')) and not any(os.environ.get(name) for name in ('GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_SERVICE_ACCOUNT_B64'))
    injected = publisher is not None
    secret = shared_secret if shared_secret is not None else os.environ.get('PLAY_HELPER_SHARED_SECRET', '')
    secret_ok = len(secret) >= 43 and not any(c.isspace() for c in secret)
    enabled = checks_enabled if checks_enabled is not None else os.environ.get('PLAY_CHECKS_ENABLED') == 'true'
    mode = purchase_mode if purchase_mode is not None else os.environ.get('PLAY_PURCHASE_MODE', 'license-test-only')
    configured = secret_ok and enabled and (injected or keyless_environment) and mode in ('license-test-only', 'all-purchases')
    package = os.environ.get('PLAY_PACKAGE_NAME', 'co.responsyve.tvremote')
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 8192
    recent, lock = deque(), threading.Lock()
    concurrent = threading.BoundedSemaphore(2)

    @app.after_request
    def response_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/health')
    def health(): return jsonify(status='ok', google_checks_configured=configured, purchase_mode=mode)

    @app.post('/internal/play/verify')
    def verify():
        nonlocal publisher
        authorization = request.headers.get('Authorization', '')
        if not secret_ok or not hmac.compare_digest(authorization.encode(), ('Bearer ' + secret).encode()):
            return jsonify(error='Unauthorized'), 401
        if request.query_string: return jsonify(error='Invalid request'), 400
        data = request.get_json(silent=True)
        token = data.get('purchaseToken') if isinstance(data, dict) else None
        if not isinstance(token, str) or not 1 <= len(token) <= 4096 or any(c.isspace() or ord(c) < 32 for c in token):
            return jsonify(error='Invalid request'), 400
        if not configured: return jsonify(error='Google Play verification is not enabled'), 503
        with lock:
            tick = time.monotonic()
            while recent and recent[0] <= tick - 60: recent.popleft()
            if len(recent) >= 60: return jsonify(error='Please retry shortly'), 429
            recent.append(tick)
        if not concurrent.acquire(blocking=False): return jsonify(error='Please retry shortly'), 429
        try:
            if publisher is None: publisher = PlayPublisher(package)
            purchase = publisher.get(token)
            # Google's authenticated response is the only authority for test status.
            # Reject real purchases before acknowledgement or any access grant.
            if mode == 'license-test-only' and not isinstance(purchase.get('testPurchase'), dict):
                return jsonify(purchase={})
            details = entitlement_details(purchase, int(clock()))
            if details is None: return jsonify(purchase={})
            expiry, base_plan = details
            acknowledgement = purchase.get('acknowledgementState')
            if acknowledgement == 'ACKNOWLEDGEMENT_STATE_PENDING': publisher.acknowledge(token)
            elif acknowledgement != 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED': return jsonify(purchase={})
            # Do not return order IDs, customer emails or unrelated Google response fields.
            return jsonify(purchase={
                'subscriptionState': purchase['subscriptionState'],
                'acknowledgementState': 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED',
                'lineItems': [{'productId': PRODUCT, 'offerDetails': {'basePlanId': base_plan},
                               'expiryTime': datetime.fromtimestamp(expiry, timezone.utc).isoformat()}],
            })
        except Exception:
            return jsonify(error='Google Play verification temporarily unavailable'), 503
        finally: concurrent.release()
    return app
