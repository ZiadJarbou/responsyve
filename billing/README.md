# TV Remote billing verification on Hyperlift

The existing Docker container runs the website on external port 8080 and a single Gunicorn worker (two threads) on loopback 127.0.0.1:9001. `scripts/start-production.mjs` supervises both; if either exits, the container exits so the platform can restart it. Private signing/Google credential variables are removed from the website child environment. This is a shared container, not a separate security boundary from the website.

Public HTTPS routes:
- POST https://responsyve.co/v1/subscription/verify
- GET https://responsyve.co/billing/health (liveness; includes configuration flag)
- GET https://responsyve.co/billing/ready (503 until explicitly configured; configuration readiness does not prove API permissions)

The fixed proxy strips client cookies, authorization headers and query strings. JSON bodies are capped at 8 KiB; upstream responses at 32 KiB. Access logging in Gunicorn is disabled. The current process has a global ceiling of 60 valid verification attempts per minute and two concurrent checks; this limits a small initial deployment and is not distributed DDoS protection. Review capacity and rate limiting before public rollout. Requests are checked against authoritative Play API status before a lease is signed. No local test purchase, mock publisher or debug entitlement is included in the production image.

## Activation — not completed

Keep BILLING_ENABLED unset/false while credentials, Console access or product setup are incomplete. The server starts with missing credentials and never grants access in that state.

In Spaceship's environment-variable editor, configure only after the owner-controlled secrets and permissions are ready:
- PLAY_PACKAGE_NAME: co.responsyve.tvremote (confirm permanent package before Play upload).
- ENTITLEMENT_PRIVATE_KEY_B64: Base64 of an owner-controlled RSA private key, at least 2048 bits, PEM PKCS8. Never commit it, send it in chat or expose it in logs.
- GOOGLE_SERVICE_ACCOUNT_B64: Base64 of the downloaded service-account JSON from an owner-controlled Google Cloud project. Only type service_account and Google's normal oauth2.googleapis.com/token URI are accepted. This is a long-lived key: prefer external workload identity if a suitable provider is established; otherwise protect, limit and rotate it. Never put this JSON in the Android app or repository.
- BILLING_ENABLED: true only after the preceding configuration and Play API access are established.

Environment changes restart the application. Use the current signed-in Spaceship UI; no extra Spaceship API key is required. Installing new credentials or granting Google Cloud/Play permissions requires the owner's participation and any platform confirmations.

Google setup: create/select a company-owned Cloud project, enable Android Publisher API, create a dedicated service identity, and grant only this app's required subscription read/acknowledgement permissions in Play Console. The Play organization account/permissions are blocked until onboarding is possible. Possessing a service-account JSON alone does not grant Play access. Do not use project Owner/Editor roles as a substitute for app-scoped Play permissions.

Use the matching RSA public key in the phone build's billingPublicKey setting; use https://responsyve.co/v1/subscription/verify for billingVerifyUrl. Leave phone checkout disabled until live product/catalog and license-tester purchase lifecycle tests pass. No server private key or Google key belongs in the APK. App configuration alone is not proof of a working subscription.

## Deployment and rollback

Build context is repository root; Dockerfile remains docker/Dockerfile; application port stays 8080. No DNS or extra subscription is needed for these routes. The existing plan's billing/renewal settings are unchanged. Gunicorn is installed in a separate venv in the image. No keys are baked into it and the container runs as the existing non-root node user.

Roll back by deploying the preceding website-only commit (328f952) if startup or page checks fail. Do not change domain connections or mail DNS. After deployment, check homepage, support/privacy/terms, health, readiness, POST malformed/disabled requests and non-POST rejection. A configured health response cannot replace a real Google Play license-test purchase, renewal, cancellation, grace/hold, refund/revocation and restore test.

Update the published privacy policy with the actual billing provider/region/retention and service activation before accepting commercial customers. Request bodies, purchase tokens, audio, text and upstream token URLs must not be logged. The app does not send voice or searches to this server. No subscription database is used; time-limited grants expire within 24 hours. Credential backup, rotation, monitoring and operational retention must be assigned to the owner before launch.
