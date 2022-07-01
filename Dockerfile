ARG PYTHON_VER=3.8

FROM python:${PYTHON_VER}-slim

RUN pip install --upgrade pip

WORKDIR /local
COPY . /local

LABEL maintainer="Khelil Sator <ksator@arista.com>"
LABEL com.example.version="0.1.0"
LABEL com.example.release-date="2022-07-01"
LABEL com.example.version.is-production="False"

RUN pip install .

CMD [ "/usr/local/bin/check-devices.py" ]
