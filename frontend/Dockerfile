# Frontend Dockerfile
FROM node:20-alpine3.21 AS build
WORKDIR /app
COPY package*.json ./
# Store the packages separately to leverage Docker cache
RUN --mount=type=cache,target=/root/.npm \
    npm i

COPY . .
RUN npm run build --prod

# Stage 2: Serve the built application using Nginx
FROM nginxinc/nginx-unprivileged:alpine3.21

# Copy built Angular app files to Nginx HTML folder
COPY --from=build /app/dist/graphrag-frontend/browser /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
# Expose port 8080
EXPOSE 8080

# Start Nginx server
# CMD ["nginx", "-g", "daemon off;"]
