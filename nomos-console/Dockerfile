# NomOS Console — Multi-stage Docker Build
FROM node:22-alpine AS deps
WORKDIR /app
COPY nomos-console/package.json nomos-console/package-lock.json ./
RUN npm ci --production=false

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY nomos-console/ ./
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nomos && \
    adduser --system --uid 1001 nomos
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nomos:nomos /app/.next/standalone ./
COPY --from=builder --chown=nomos:nomos /app/.next/static ./.next/static
USER nomos
EXPOSE 3000
CMD ["node", "server.js"]
