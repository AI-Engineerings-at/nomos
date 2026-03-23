FROM node:22-slim AS builder

WORKDIR /app
COPY nomos-console/package.json nomos-console/package-lock.json* ./
RUN npm ci
COPY nomos-console/ .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3040
ENV HOSTNAME="0.0.0.0"

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

RUN adduser --disabled-password --no-create-home --gecos "" nomos
USER nomos

EXPOSE 3040
CMD ["node", "server.js"]
