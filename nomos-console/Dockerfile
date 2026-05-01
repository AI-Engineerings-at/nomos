# NomOS Console — Multi-stage Docker Build
FROM node:22-alpine AS deps
WORKDIR /app
COPY nomos-console/package.json nomos-console/package-lock.json ./
RUN npm ci --production=false

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY nomos-console/ ./
ENV NOMOS_API_URL=http://nomos-api:8000
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
RUN addgroup --system --gid 1001 nomos && \
    adduser --system --uid 1001 nomos
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nomos:nomos /app/.next ./.next
COPY --from=builder --chown=nomos:nomos /app/package.json ./package.json
COPY --from=builder --chown=nomos:nomos /app/package-lock.json ./package-lock.json
RUN npm ci --omit=dev
USER nomos
EXPOSE 3000
CMD ["sh", "-c", "npm run start || while true; do sleep 30; done"]
