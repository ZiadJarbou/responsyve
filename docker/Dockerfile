FROM node:24-bookworm-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# Keep native compiler pools small on Hyperlift Micro's fractional CPU.
ENV NITRO_PRESET=node-server \
    RAYON_NUM_THREADS=1 \
    ROLLDOWN_WORKER_THREADS=1 \
    ROLLDOWN_MAX_BLOCKING_THREADS=2
RUN npm run build

FROM node:24-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=8080
COPY --from=build --chown=node:node /app/.output ./.output
USER node
EXPOSE 8080
CMD ["node", ".output/server/index.mjs"]
