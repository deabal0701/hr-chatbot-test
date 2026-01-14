# MUREUM Frontend Dockerfile
# Multi-stage build for optimized production image

FROM node:20.18-alpine AS builder

# Build argument to select environment file
ARG ENV_FILE=.env.docker

# Set working directory
WORKDIR /app

# Install dependencies first (better cache utilization)
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Copy environment file and build
RUN cp ${ENV_FILE} .env.production
RUN npm run build

# Production stage
FROM nginx:alpine

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/*

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 18080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
