ARG PYTHON_VER=3.9
ARG IMG_OPTION=alpine

### BUILDER

FROM python:${PYTHON_VER}-${IMG_OPTION} AS BUILDER

RUN pip install --upgrade pip

WORKDIR /local
COPY . /local

RUN python -m venv /opt/venv


ENV PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache build-base # Add build-base package
RUN pip --no-cache-dir install "." &&\
    pip --no-cache-dir install ".[cli]"

# ----------------------------------- #

### BASE

FROM python:${PYTHON_VER}-${IMG_OPTION} AS BASE

# Add a system user
RUN adduser --system anta

# Opencontainer labels
# Labels version and revision will be updating
# during the CI with accurate information
# To configure version and revision, you can use:
# docker build --label org.opencontainers.image.version=<your version> -t ...
# Doc: https://docs.docker.com/engine/reference/commandline/run/#label
LABEL   "org.opencontainers.image.title"="anta" \
        "org.opencontainers.artifact.description"="network-test-automation in a Python package and Python scripts to test Arista devices." \
        "org.opencontainers.image.description"="network-test-automation in a Python package and Python scripts to test Arista devices." \
        "org.opencontainers.image.source"="https://github.com/arista-netdevops-community/anta" \
        "org.opencontainers.image.url"="https://www.anta.ninja" \
        "org.opencontainers.image.documentation"="https://www.anta.ninja" \
        "org.opencontainers.image.licenses"="Apache-2.0" \
        "org.opencontainers.image.vendor"="The anta contributors." \
        "org.opencontainers.image.authors"="Khelil Sator, Angélique Phillipps, Colin MacGiollaEáin, Matthieu Tache, Onur Gashi, Paul Lavelle, Guillaume Mulocher, Thomas Grimonet" \
        "org.opencontainers.image.base.name"="python" \
        "org.opencontainers.image.revision"="dev" \
        "org.opencontainers.image.version"="dev"

# Copie les fichiers nécessaires depuis l'image BUILDER
COPY --from=BUILDER /opt/venv /opt/venv

# Définit l'utilisateur et le PATH
# USER anta
ENV PATH="/opt/venv/bin:$PATH"

USER anta

# Définition du point d'entrée
ENTRYPOINT [ "/opt/venv/bin/anta" ]
