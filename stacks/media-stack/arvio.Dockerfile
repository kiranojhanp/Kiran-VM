# syntax=docker/dockerfile:1
# Native build of ProdigyV21/ARVIO web app from source.
# There is no prebuilt official image, so we clone and build the Next.js standalone
# output here, mirroring the upstream web/Dockerfile runtime (/app standalone, PORT 3000).

FROM node:22-bookworm-slim AS base
ARG ARVIO_REF=main
ARG ARVIO_REPO=https://github.com/ProdigyV21/ARVIO.git

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${ARVIO_REF}" "${ARVIO_REPO}" /arvio

FROM base AS dependencies
WORKDIR /arvio/web
RUN npm ci

FROM dependencies AS builder
ARG TRAKT_CLIENT_ID=""
ARG SIMKL_CLIENT_ID=""
ARG NEXT_PUBLIC_TELEGRAM_API_ID=""
ARG NEXT_PUBLIC_TELEGRAM_API_HASH=""
ARG NEXT_PUBLIC_ARVIO_RESOLVER_URL=""
ENV NEXT_PUBLIC_SELF_HOSTED=true \
    NEXT_PUBLIC_PAYWALL_ENABLED=false \
    ARVIO_STANDALONE=true \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_TRAKT_CLIENT_ID=$TRAKT_CLIENT_ID \
    NEXT_PUBLIC_SIMKL_CLIENT_ID=$SIMKL_CLIENT_ID \
    NEXT_PUBLIC_TELEGRAM_API_ID=$NEXT_PUBLIC_TELEGRAM_API_ID \
    NEXT_PUBLIC_TELEGRAM_API_HASH=$NEXT_PUBLIC_TELEGRAM_API_HASH \
    NEXT_PUBLIC_ARVIO_RESOLVER_URL=$NEXT_PUBLIC_ARVIO_RESOLVER_URL
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_SELF_HOSTED=true \
    NEXT_PUBLIC_PAYWALL_ENABLED=false \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=builder --chown=node:node /arvio/web/.next/standalone ./
COPY --from=builder --chown=node:node /arvio/web/.next/static ./.next/static
COPY --from=builder --chown=node:node /arvio/web/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]