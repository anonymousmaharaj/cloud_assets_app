FROM ubuntu

ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV PYTHONUNBUFFERED = 1
RUN apt update && apt -y upgrade
RUN apt install python3-pip python3-dev nano libpq-dev nginx curl -y

WORKDIR /usr/src/app

COPY . .
RUN pip3 install -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

