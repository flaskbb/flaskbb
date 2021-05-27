FROM python:3.8-alpine

LABEL maintainer="luisito666 <luispenagos91@gmail.com>"

ENV FLASK_ENV=development

RUN apk update \
    && apk add postgresql-dev bash linux-headers\
    && pip install -U pip \
    && mkdir -p /app

COPY . /app

WORKDIR /app

RUN set -ex \
    && apk add zlib-dev jpeg-dev git \
    && apk add --no-cache --virtual .build-deps build-base \
    && pip install -r requirements-dev.txt \
    && pip install psycopg2 \
    && apk del .build-deps


RUN echo 'export PS1="\[\e[36m\]flaskbb>\[\e[m\] "' >> /root/.bashrc
RUN echo 'export PYTHONPATH="${PYTHONPATH}:/app/"' >> /root/.bashrc
RUN echo 'function flaskbb_local { flaskbb --config flaskbb-dev.cfg run --host=0.0.0.0; }' >> /root/.bashrc

COPY ./docker/dev/start /
RUN chmod +x /start

CMD ["/start"]
