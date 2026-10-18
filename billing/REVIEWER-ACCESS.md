# Reviewer access â€” implemented, activation pending

Google's [review-access requirements](https://support.google.com/googleplay/android-developer/answer/15748846) call for reusable, geographically unrestricted credentials that allow full access without reviewer payment. This app provides a visible **Reviewer access** button on its subscription screen. It is an authenticated support/review grant, not a price or purchase override.

## Access mechanism

The reviewer enters a 43-character random code supplied privately in Play Console. The app sends it over HTTPS to the existing verification endpoint with an installation identifier and fresh nonce. The server stores only the code's SHA-256 digest in configuration and uses constant-time comparison. The code is not embedded in the app, listing assets, public website or source archive. No OTP, email verification, payment card, purchase or geographic check is required.

A valid code produces a signed, installation/nonce/package-scoped **tv_remote_reviewer** grant for ten minutes. The app verifies its signature using the public entitlement key, refreshes it while foregrounded and stores the credential only in private, backup-disabled app storage so the reviewer can reopen the app. Reboot requires online revalidation. The normal paid grant uses a separate product scope and storage. Restoring an empty Play purchase list cannot delete the reviewer grant, and a reviewer grant cannot masquerade as a paid subscription.

The full existing remote opens after authentication, including real TV discovery/pairing, keys, touchpad, numbers, keyboard, voice, shortcuts and Arabic YouTube search. The app does not fake a TV or a purchase. Reviewers still need a compatible powered-on Android TV/Google TV and a local network that permits discovery.

**End reviewer access** is available on the TV selection screen while the grant is active. It clears the local reviewer credential/grant without changing a paid subscription or saved TV pairings. Normal users still require Google Play subscription access unless they possess the private review credential.

## Activation handoff

1. Review and deploy the dedicated `reviewer-access` website branch. It contains only reviewer-server support on the existing production base; it excludes the pending Cloud Run helper changes. Merely deploying it leaves review access disabled by default.
2. Enter the private environment configuration through Spaceship: `REVIEWER_CREDENTIAL_SHA256`, `REVIEWER_ACCESS_ENABLED=true`, and the existing matching signing key using `ENTITLEMENT_PRIVATE_KEY_B64_1`, `_2`, and `_3` (four chunks are supported). Keep **BILLING_ENABLED=false** until normal production verification is ready. The reviewer endpoint can operate without Play API credentials or Cloud Billing.
3. Private handoff files are in the ignored `release-secrets/reviewer` directory. The split signing-key handoff is `spaceship-signing-key-parts.txt` in that same private folder; each value fits Spaceship's 1,024-character limit. Do not add these files to an archive, issue, screenshot or chat.
4. Verify live HTTPS acceptance, invalid-code rejection and the final app's successful reviewer login. Test restart/refresh, end access and code rotation on a disposable test installation. Customer checkout stays disabled during this work.
5. Add the private code to **Play Console â†’ App content â†’ Sign-in details / App access**, with the instructions below. No Play Console submission is possible until organization onboarding completes. Keep this credential working for subsequent reviews; avoid auto-expiry or requiring a response from the owner.

Reviewer access is **not yet configured live or submitted to Play Console**. Local implementation and tests do not clear those gates.

## Instructions to paste into Play Console

Instruction name: **Full remote access for Google Play review**

Username: **Not required â€” use the Reviewer access button**

Access code/password: **Insert the private value from play-console-code.txt here; never publish it in the store listing.**

Additional instructions:

> On the subscription screen tap Reviewer access, enter the supplied reusable access code, then tap Continue. No subscription, payment card, personal purchase, OTP or Responsyve account is required. Internet is needed to verify and renew review access. This code is usable across reviewer locations and installations.
>
> Connect the phone and a powered-on Android TV/Google TV to the same local network. Select the TV and enter the pairing code shown on the TV; this TV-generated code authorizes hardware control and is separate from reviewer login. Developer mode, ADB and TV companion installation are not required.
>
> Test directional/OK, Back, Apps, Voice, Home, volume/mute and playback. The four mode icons select Buttons, Touchpad, Numbers and Keyboard. Allow microphone permission to test Voice. In Keyboard mode type Ù…Ø±Ø­Ø¨Ø§ and tap Search YouTube to open Arabic results on the TV. YouTube must be installed. Live text editing and some commands depend on the TV/receiving app. Privacy, terms and support are available without purchase. End reviewer access is on the TV selection page.
>
> This grant unlocks every remote feature. It does not create a Google Play purchase; checkout/restore behavior remains the normal Google Play flow and can be tested separately using the configured Play test setup.

## Revocation and operations

Disable `REVIEWER_ACCESS_ENABLED` or replace the server hash to revoke the old code. Restart/redeploy the service after environment edits. Existing grants remain valid for at most ten minutes from issuance, then require revalidation; revocation is not instantaneous for an offline phone. Maintain reusable working review credentials in Console whenever Google may review the app. Update Console instructions when rotating them. Do not log request bodies, credentials, purchase tokens or signed grants. The current single-worker server caps reviewer attempts globally at 30 per minute; review capacity before increasing deployment scale.

## Validation

Thirty backend tests pass, including six reviewer cases: reusable signed scope without Play/payment, disabled/missing/rotated configuration, invalid credentials/identifiers, purchase-route separation rate limiting, and split-key configuration. Android emulator checks cover signature/nonce/scope/expiry/reboot rules plus reviewer/paid separation, ten-minute bounds and local logout. Release build/lint pass. Live deployment, live login and Play reviewer instructions are still pending.
