FROM python:3.8.2-buster

RUN apt -y update && \
    apt -y upgrade && \
    apt -y install ffmpeg

ENV PYTHONUNBUFFERD 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /code

RUN mkdir /code/
WORKDIR /code
COPY .devcontainer/requirements.txt /code

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt