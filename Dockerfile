FROM python:3
MAINTAINER Travis Paquette "tpaqu15@gmail.com"
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD python app.py
