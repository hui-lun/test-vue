FROM node:20-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# FROM node:20-alpine
# WORKDIR /app
# COPY package*.json ./
# RUN npm install
# EXPOSE 8080
# CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]
