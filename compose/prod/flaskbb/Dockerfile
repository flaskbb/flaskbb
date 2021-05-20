FROM python:3.8-alpine

LABEL maintainer="luisito666 <luispenagos91@gmail.com>"

RUN apk update \
    && apk add postgresql-dev bash\
    && pip install -U pip \
    && mkdir -p /app

COPY . /app

WORKDIR /app

RUN set -ex \
    && apk add zlib-dev jpeg-dev \
    && apk add --no-cache --virtual .build-deps build-base git\
    && pip install -r requirements.txt \
    && pip install gunicorn psycopg2 \
    && apk del .build-deps


RUN echo 'export PS1="\[\e[36m\]flaskbb>\[\e[m\] "' >> /root/.bashrc

COPY ./compose/prod/flaskbb/start /
RUN chmod +x /start

CMD ["/start"]
