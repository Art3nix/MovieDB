
FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

EXPOSE 8000