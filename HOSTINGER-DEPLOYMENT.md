# Hostinger deployment

Responsyve's Node website and Python TV Remote verification service run on the
existing Hostinger VPS `187.127.172.28` (Mumbai, India). This preserves the two
runtimes used by the original container. KarCast has a separate Nginx virtual
host on the same VPS.

## Services and files

- Website: `responsyve-website.service`, listening only on `127.0.0.1:8080`.
- Verification: `responsyve-billing.service`, listening only on
  `127.0.0.1:9001`, one Gunicorn worker and two threads.
- Public HTTPS: Nginx virtual host `/etc/nginx/sites-available/responsyve`.
- Runtime source: `/opt/responsyve/current`, a symlink into
  `/opt/responsyve/releases/`.
- Node 24 LTS: `/opt/responsyve-node/`; Python environment:
  `/opt/responsyve/venv/`.
- Existing billing/reviewer settings: `/etc/responsyve/billing.env`, owned by
  root with mode `0600`. Systemd supplies these only to the billing service;
  the website service does not receive the signing key or reviewer hash.

The migrated configuration keeps paid billing disabled and preserves reviewer
access. No private keys, reviewer credentials or environment files belong in
this repository. Real Google Play purchase verification still requires its
separate activation and license-test checks.

## GitHub deployment

With the owner's approval, `responsyve-deploy.timer` checks this repository's
public `main` branch every five minutes. Its root-owned deployment script is
`/usr/local/sbin/responsyve-deploy-latest`. Builds execute as the unprivileged
`responsyve` user with small native compiler pools. A successful new release
restarts the two services. Failed homepage/health checks restore the previous
release symlink. Prior release directories remain available for rollback;
monitor disk usage and remove obsolete releases deliberately.

Inspect deployment results with:

```sh
systemctl status responsyve-website responsyve-billing
journalctl -u responsyve-deploy.service --since today
systemctl list-timers responsyve-deploy.timer
```

The shared Python environment is reused between releases. For a dependency
upgrade, review Python package compatibility before relying on rollback.

## DNS and HTTPS

The intended Hostinger DNS records are:

| Type | Name | Value | TTL |
| --- | --- | --- | --- |
| A | @ | 187.127.172.28 | 300 |
| CNAME | www | responsyve.co | 300 |
| MX | @ | smtp.google.com, priority 1 | 300 |
| TXT | @ | Existing Google site verification value | 1800 |

The domain transfer and owner-email verification completed on 19 October 2026.
Nameservers are `apollo.dns-parking.com` and `athena.dns-parking.com`; the .co
registry delegates to them. The website, Google MX and Google verification
records were checked directly on these nameservers. Preserve these Google
records when changing DNS. DNSSEC remains disabled as requested. Resolver
caches can temporarily retain the former Spaceship addresses during cutover.

The certificate covers `responsyve.co` and `www.responsyve.co` and is installed
at `/etc/letsencrypt/live/responsyve.co/`. Initial issuance used DNS validation
before cutover. Certbot's automatic HTTP renewal test subsequently passed and
saved the webroot `/var/www/responsyve-acme`, HTTP challenge preference, and
Nginx reload hook. `certbot.timer` is enabled. The certificate no longer relies
on manual DNS challenges for renewal.

## Checks

Verify the homepage, `/tv-remote/support/`, `/tv-remote/privacy/`,
`/tv-remote/terms/`, and `/billing/health`. While paid billing is disabled,
`/billing/ready` correctly returns 503. GET requests to the verification route
must return 405 and malformed JSON requests must be rejected. Run the existing
Python reviewer tests and Node proxy/environment tests after relevant changes.

The original Hyperlift app has not been deleted or its subscription cancelled.
Use it only as a deliberate rollback option; never put secret values in logs,
screenshots or deployment notes.

## Cloud Run purchase helper — 21 October 2026

The keyless helper is deployed in europe-west1 (Belgium). Configure only the
billing service environment in `/etc/responsyve/billing.env`:

- `PLAY_HELPER_URL=https://tv-remote-play-helper-1043064764898.europe-west1.run.app/internal/play/verify`
- `PLAY_HELPER_SHARED_SECRET`: the owner-controlled gateway secret already in
  Google Secret Manager, version 1. Never put its value in Git or logs.
- `BILLING_ENABLED=false` until Play organization onboarding, app-scoped API
  permissions, subscription catalog and license-test lifecycle checks pass.

Preserve reviewer access settings and existing RSA signing key parts. The
website service must not receive the gateway secret. The verifier refuses
redirects and requires the fixed HTTPS Cloud Run verification path. It forwards
only the purchase token, then signs an access grant locally after validating
subscription state. Cloud Run currently has `PLAY_CHECKS_ENABLED=false`, so
real purchases cannot grant access through this path yet.

The helper has no RSA signing key or customer database. Normal Cloud Logging
retention is 30 days; required audit retention is 400 days, at global location.
On the VPS, Nginx uses daily rotation with 14 rotated log files retained and
journald has a 1 GB size limit, not a fixed retention duration. Verification
access logging is off at Nginx and Gunicorn. No provider-wide purge is implied.
