FROM node:boron

RUN mkdir /app && mkdir /app/django-edw

WORKDIR /app/

COPY frontend/package.json .

RUN npm install

ENV PATH /app/node_modules/.bin:/app/node_modules:/app/django-edw:$PATH