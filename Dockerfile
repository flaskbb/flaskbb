FROM smebberson/alpine-nginx:latest
MAINTAINER battlecat <17527695@qq.com>
RUN apk update
RUN apk add gcc make python py-pip jpeg libjpeg jpeg-dev zlib zlib-dev tiff freetype git py-pillow python-dev musl bash  
RUN copy . /home/flaskbb/
WORKDIR /home/flaskbb
RUN pip install -r /requirements-dev.txt
RUN pip instal gunicorn
RUN flaskbb makeconfig -d
RUN flaskbb --config ./flaskbb.cfg install
CMD flaskbb start
