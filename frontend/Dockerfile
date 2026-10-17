FROM node:24-alpine AS base
WORKDIR /app
RUN addgroup -g 1001 appgroup && \
    adduser -D -u 1001 -G appgroup appuser

FROM base AS dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --frozen-lockfile
COPY frontend/ .
RUN npm ci --frozen-lockfile

FROM base AS builder
COPY --from=dependencies /app/node_modules ./node_modules
COPY frontend/ .
RUN npm run build

FROM base AS runtime
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:3000/ || exit 1
CMD ["npx", "vite", "preview", "--host", "127.0.0.1", "--port", "3000"]