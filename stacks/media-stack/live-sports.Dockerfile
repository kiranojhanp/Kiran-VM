# syntax=docker/dockerfile:1
# Native arm64 build of rajhodedara/live-sport-plugin.
# The published ghcr.io image is amd64-only, so we build from source here.
# Result mirrors the upstream Dockerfile's runtime layout (/app/dist, /app/public, /app/resolver).

FROM node:22-slim AS builder

ARG PLUGIN_REF=main
ARG PLUGIN_REPO=https://github.com/rajhodedara/live-sport-plugin.git

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${PLUGIN_REF}" "${PLUGIN_REPO}" /plugin

WORKDIR /plugin
RUN npm install \
    && cd resolver && npm install && cd .. \
    && npm run build

FROM node:22-slim

WORKDIR /app
COPY --from=builder /plugin ./

ENV PORT=7000
ENV NODE_ENV=production
EXPOSE 7000
CMD ["node", "dist/index.js"]