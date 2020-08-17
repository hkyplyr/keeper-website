FROM ubuntu:18.04

MAINTAINER Travis Paquette "tpaqu15@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3.6 python3-pip
RUN python3.6 --version
RUN pip3 --version

COPY ./requirements.txt usr/src/app/requirements.txt

WORKDIR /usr/src/app

RUN pip3 install -r requirements.txt

COPY . /usr/src/app

ENTRYPOINT [ "python3.6" ]
CMD [ "app.py" ]
