ARG PYTHON_VER=3.9

FROM python:${PYTHON_VER}-slim

RUN pip install --upgrade pip

WORKDIR /local
COPY . /local

ENV PYTHONPATH=/local
RUN pip --no-cache-dir install .

# Opencontainer labels
LABEL   "org.opencontainers.image.title"="anta" \
        "org.opencontainers.artifact.description"="network-test-automation in a Python package and Python scripts to test Arista devices." \
        "org.opencontainers.image.source"="https://github.com/arista-netdevops-community/anta" \
        "org.opencontainers.image.url"="https://www.anta.ninja" \
        "org.opencontainers.image.documentation"="https://www.anta.ninja" \
        "org.opencontainers.image.licenses"="Apache-2.0" \
        "org.opencontainers.image.vendor"="The anta contributors." \
        "org.opencontainers.image.authors"="Khelil Sator, Angélique Phillipps, Colin MacGiollaEáin, Matthieu Tache, Onur Gashi, Paul Lavelle, Guillaume Mulocher, Thomas Grimonet" \
        "org.opencontainers.image.base.name"="python" \
        "org.opencontainers.image.revision"="" \
        "org.opencontainers.image.version"=""

ENTRYPOINT [ "/usr/local/bin/anta" ]
