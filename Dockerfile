FROM python:3.5


RUN apt-get update && apt-get install -qq -y build-essential --fix-missing --no-install-recommends

ENV INSTALL_PATH /flaskbb
ENV TERM xterm

RUN mkdir -p $INSTALL_PATH
WORKDIR  $INSTALL_PATH

COPY . .

RUN pip install -r requirements.txt

RUN make uinstall

VOLUME ["$INSTALL_PATH/build/public"]

CMD python manage.py runserver -dr -p 8000  -h 0.0.0.0
