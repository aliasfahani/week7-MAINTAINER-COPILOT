FROM nginx:1.27-alpine
COPY frontend/host/index.html /usr/share/nginx/html/index.html
COPY frontend/host/nginx.conf /etc/nginx/conf.d/default.conf
