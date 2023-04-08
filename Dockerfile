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

LABEL org.opencontainers.image.title ANTA
LABEL org.opencontainers.artifact.description "network-test-automation in a Python package and Python scripts to test Arista devices."
LABEL org.opencontainers.image.url https://www.anta.ninja
LABEL org.opencontainers.image.documentation https://www.anta.ninja
LABEL org.opencontainers.image.licenses APACHE2
LABEL org.opencontainers.image.authors "Khelil Sator, Angélique Phillipps, Colin MacGiollaEáin, Matthieu Tache, Onur Gashi, Paul Lavelle, Guillaume Mulocher, Thomas Grimonet"
LABEL org.opencontainers.image.base.name python
LABEL org.opencontainers.image.source https://github.com/arista-netdevops-community/anta

ENTRYPOINT [ "/usr/local/bin/anta" ]
