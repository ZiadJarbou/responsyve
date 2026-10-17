# Responsyve app pages — local review draft

No hosting or DNS changes made. Public email supplied by owner: info@responsyve.co. Mail reception has not been tested.

Proposed public URLs:
- https://responsyve.co/tv-remote/privacy/
- https://responsyve.co/tv-remote/terms/
- https://responsyve.co/tv-remote/support/

The three generated pages are in `public/tv-remote/`. They are served by the existing Nitro production server, with no new package dependencies. Responsive HTML/CSS includes accessible navigation, print styling and cross-page links. The editable source drafts and generator are retained in the TV Remote project under `release/legal-drafts/` and `release/website/`. The review banner, pending fields and noindex are deliberate; these drafts are not live policies.

Before publication:
- Supply registered mailing address, effective date, intended audience and business/legal review of applicable privacy/consumer terms. Do not invent a street address, liability waiver or court venue.
- Verify the mailbox, assign privacy/support ownership and set support correspondence retention and response expectations.
- Choose the verification host, regions, operational metadata/logging and retention. Confirm international processing safeguards and Google Workspace mailbox retention. Exclude purchase tokens, request bodies, text and audio from server logs.
- Review final Play Billing SDK disclosures and release SDK inventory against Data safety answers. Avoid a blanket no-data-collected claim.
- Confirm live subscription, localized prices, cancellation/refund/restore behavior and help links; replace pre-release wording when accurate.
- Hosting confirmed through the signed-in dashboard: Spaceship Hyperlift Micro, GitHub repository ZiadJarbou/responsyve, main branch, docker/Dockerfile. The unrelated Web Hosting Essential package has zero connected domains. Do not connect the domain there or alter mail DNS. Hyperlift currently marks its latest deployment as failed even though the supplied log reaches successful compilation and image push; the underlying deployment failure has not been diagnosed.
- Resolve all pending fields, set effective date, remove draft banner/noindex and verify final public HTTPS pages return 200 without login. Then configure app privacyUrl/termsUrl and rebuild.
- Correct commercial in-app privacy wording: MainActivity currently contains development text saying no subscriptions. This is recorded as a release blocker; no app code changed in this task.

Sources reviewed 17 October 2026:
- https://support.google.com/googleplay/android-developer/answer/10144311
- https://support.google.com/googleplay/android-developer/answer/9900533
- https://support.google.com/googleplay/answer/7018481
- App manifest, DeviceStore, Identity, MainActivity, VoiceCapture, PlaySubscription, SubscriptionLease, YoutubeSearchLink and backend code.

Older release ZIPs have not been overwritten. No phone installation or saved pairing changed. This preparation is not a legal compliance certification.

## Integration validation

TypeScript check passed. The npm build wrapper fails on Windows with `spawn vite ENOENT`; running the same locked Vite CLI directly completed the client, SSR and Nitro node-server production build. Migration script completed with no configured database and no migration performed. Production server smoke checks passed for the existing homepage, all three trailing-slash page routes and stylesheet. Homepage source and deploy configuration are unchanged. Public publishing, legal approval and final mailbox verification are pending.
