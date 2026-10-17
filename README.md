# Responsyve

Company site for Responsyve — software, commerce, and brand.

Products: [KarCast](https://karcast.app) and [LeafletAI](https://leafletai.ai).

Studio: Dubai, United Arab Emirates. Contact: info@responsyve.co

## Develop

```bash
npm install
npm run dev
```

The dev server listens on port 8080.

## Deploy on Hyperlift

Connect the `main` branch and set the Dockerfile path to `docker/Dockerfile`
with the repository root as the build context. Set the application port to
`8080`. The image builds the Nitro Node server and runs it as the unprivileged
`node` user, listening on `0.0.0.0:8080`.

To build and start the production server without Docker:

```sh
npm ci
npm run build
HOST=0.0.0.0 PORT=8080 npm start
```

The default Nitro preset is `node-server`; set `NITRO_PRESET=vercel` for a
Vercel build. Keep runtime secrets in the hosting environment, outside the
image. If database features are added, configure a persistent `DATABASE_URL`
and run `npm run db:migrate` against it before deployment; the unconfigured
PGLite fallback stores data in memory only.
