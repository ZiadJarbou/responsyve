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
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/billing-venv
COPY billing/requirements.txt /app/billing/requirements.txt
RUN /opt/billing-venv/bin/pip install --no-cache-dir -r /app/billing/requirements.txt
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=8080
COPY --from=build --chown=node:node /app/.output ./.output
COPY --chown=node:node billing/app.py /app/billing/app.py
COPY --chown=node:node scripts/start-production.mjs /app/scripts/start-production.mjs
USER node
EXPOSE 8080
CMD ["node", "scripts/start-production.mjs"]
