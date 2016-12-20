FROM python:2.7
ENV PYTHONUNBUFFERED 1

COPY . /application
RUN pip install -r requirements.txt

WORKDIR /application
