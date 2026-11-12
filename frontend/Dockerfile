# Stage 1: Build the React application
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --cache /root/.npm

COPY . .
RUN npm run build

# Stage 2: Serve static files with lightweight Nginx (Free Tier optimized: ~10MB RAM)
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
