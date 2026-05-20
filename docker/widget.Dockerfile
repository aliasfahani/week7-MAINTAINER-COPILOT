FROM node:20-slim
WORKDIR /app
COPY frontend/widget/package.json frontend/widget/package.json
RUN cd frontend/widget && npm install
COPY frontend/widget .
WORKDIR /app/frontend/widget
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
