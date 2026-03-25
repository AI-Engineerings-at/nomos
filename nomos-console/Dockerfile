# NomOS Console — Docker Build
FROM node:22-alpine
WORKDIR /app
COPY nomos-console/package.json nomos-console/package-lock.json ./
RUN npm ci
COPY nomos-console/ ./
RUN npm run build
ENV NODE_ENV=production
ENV NOMOS_API_URL=http://nomos-api:8000
EXPOSE 3000
CMD ["npm", "start"]
