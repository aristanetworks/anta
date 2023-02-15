ARG PYTHON_VER=3.9

FROM python:${PYTHON_VER}-slim

RUN pip install --upgrade pip

WORKDIR /local
COPY . /local

LABEL maintainer="Khelil Sator <ksator@arista.com>"
LABEL com.example.version="0.4.0"
LABEL com.example.release-date="2023-02-16"
LABEL com.example.version.is-production="False"

ENV PYTHONPATH=/local
RUN pip --no-cache-dir install .

ENTRYPOINT [ "/usr/local/bin/anta" ]
