FROM node:lts AS builder
WORKDIR /build
COPY . .
RUN npm install
RUN npm run build

FROM nginx:alpine AS runner
RUN echo "worker_processes 4;\n\
events{worker_connections 1024;}\n\
http{server{listen 80; root /webflow; include /etc/nginx/mime.types; location / {try_files \$uri /index.html;} } }" > /etc/nginx/nginx.conf

WORKDIR /webflow
COPY --from=builder /build/dist/webflow .

EXPOSE 80

ENTRYPOINT [ "nginx", "-g", "daemon off;" ]

