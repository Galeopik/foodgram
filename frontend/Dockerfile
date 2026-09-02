# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build
CMD ["sh", "-c", "rm -rf result_build/* && cp -r build/. result_build/"]
