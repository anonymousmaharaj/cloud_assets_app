FROM python:3

ENV TZ=UTC
ENV DB_PASSWORD=Annonnymous_1488
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && apt -y upgrade
RUN apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib postgresql-client nginx curl gunicorn -y

USER postgres

RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE DATABASE cloud_assets;"


WORKDIR /usr/src/app

COPY . .
RUN pip3 install -r requirements.txt

COPY docker/nginx/nginx.conf /etc/nginx/conf.d

COPY entrypoint.sh /docker-entrypoint.d

EXPOSE 8000

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

