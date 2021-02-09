FROM python:3.7.4-slim-stretch

LABEL maintainer "Alexander Rainchik<rainchik>"
ENV LANG=en_US.UTF-8
WORKDIR /home/ubuntu
#separate layer with requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD [ "python","bazaraki.py" ]
