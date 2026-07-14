FROM --platform=amd64 python:3.11-slim-bookworm

# Install packages
RUN apt-get update && apt-get install -y build-essential

RUN pip install --upgrade pip setuptools wheel

WORKDIR /web_app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENV PYTHONPATH="/web_app/"
ENV FLASK_APP=manage.py
EXPOSE 5000

