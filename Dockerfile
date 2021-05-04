FROM ubuntu:20.04

ENV PYTHONIOENCODING = utf-8

RUN apt-get update -y
RUN apt-get install python3 -y
RUN apt-get install tzdata -y
RUN apt-get install python3-pip -y

RUN cp /usr/share/zoneinfo/Asia/Seoul /etc/localtime
RUN echo "Asia/Seoul" > /etc/timezone

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install pyyaml
RUN pip3 install boto3
RUN pip3 install pytest
RUN pip3 install ccxt
RUN pip3 install simple_utils
RUN pip3 install aws_glove


CMD ["cd /app", "python3 app.py"]
