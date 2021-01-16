FROM ubuntu:18.04

MAINTAINER Travis Paquette "tpaqu15@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3.8 python3-pip

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY ./requirements.txt usr/src/app/requirements.txt

WORKDIR /usr/src/app

RUN pip3 install -r requirements.txt

COPY ./keeper-website /usr/src/app

CMD [ "flask", "run", "--host=0.0.0.0" ]
