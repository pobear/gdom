FROM python:2.7
ENV PYTHONUNBUFFERED 1

COPY . /app
RUN pip install -r /requirements.txt

WORKDIR /app
