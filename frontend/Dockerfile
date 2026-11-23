FROM node:20-alpine AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 10001 civiclens && adduser --system --uid 10001 --ingroup civiclens civiclens
COPY --from=builder --chown=civiclens:civiclens /app/public ./public
COPY --from=builder --chown=civiclens:civiclens /app/.next/standalone ./
COPY --from=builder --chown=civiclens:civiclens /app/.next/static ./.next/static
USER civiclens
EXPOSE 3000
CMD ["node", "server.js"]
