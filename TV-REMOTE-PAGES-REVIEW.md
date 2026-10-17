# TV Remote app pages

Public routes: /tv-remote/privacy/, /tv-remote/terms/, /tv-remote/support/.

Contact: info@responsyve.co. Registered address confirmed by the owner: Business Centre, 3 Floor, Building A3, Business Park, Dubai South, Dubai, UAE. Page effective date: 17 October 2026.

The pages distinguish the working development app from the planned commercial Play release. The subscription is not live and the verification backend is not deployed. Provider/processing details must be added before enabling commercial access; live billing tests and Data safety review remain release blockers. A website publication is not evidence of a completed Play release or legal compliance certification.

The existing homepage gains a TV Remote support footer link. Existing product content and hosting configuration are preserved. The pages use public static files, no new dependencies, forms or trackers.

Validation: TypeScript check and direct locked Vite production build passed. Production Node server smoke checks covered the homepage, all three trailing-slash page URLs and shared CSS. The existing npm build wrapper fails to spawn the Windows Vite shim, so local builds use node node_modules/vite/bin/vite.js build followed by node scripts/migrate.mjs. Linux Docker build uses the original npm script.
