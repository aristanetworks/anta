ARG PYTHON_VER=3.9.18
ARG IMG_OPTION=alpine3.18

### BUILDER

FROM python:${PYTHON_VER}-${IMG_OPTION} as BUILDER

RUN pip install --upgrade pip

WORKDIR /local
COPY . /local

ENV PYTHONPATH=/local
ENV PATH=$PATH:/root/.local/bin

RUN pip --no-cache-dir install --user .

# ----------------------------------- #

### BASE

FROM python:${PYTHON_VER}-${IMG_OPTION} as BASE

# Opencontainer labels
# Labels version and revision will be updating
# during the CI with accurate information
# To configure version and revision, you can use:
# docker build --label org.opencontainers.image.version=<your version> -t ...
# Doc: https://docs.docker.com/engine/reference/commandline/run/#label
LABEL   "org.opencontainers.image.title"="anta" \
        "org.opencontainers.artifact.description"="network-test-automation in a Python package and Python scripts to test Arista devices." \
        "org.opencontainers.image.source"="https://github.com/arista-netdevops-community/anta" \
        "org.opencontainers.image.url"="https://www.anta.ninja" \
        "org.opencontainers.image.documentation"="https://www.anta.ninja" \
        "org.opencontainers.image.licenses"="Apache-2.0" \
        "org.opencontainers.image.vendor"="The anta contributors." \
        "org.opencontainers.image.authors"="Khelil Sator, Angélique Phillipps, Colin MacGiollaEáin, Matthieu Tache, Onur Gashi, Paul Lavelle, Guillaume Mulocher, Thomas Grimonet" \
        "org.opencontainers.image.base.name"="python" \
        "org.opencontainers.image.revision"="dev" \
        "org.opencontainers.image.version"="dev"

COPY --from=BUILDER /root/.local/ /root/.local
ENV PATH=$PATH:/root/.local/bin

ENTRYPOINT [ "/root/.local/bin/anta" ]
