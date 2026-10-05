ARG PYTHON_VER=3.10
ARG IMG_OPTION=alpine
ARG UV_VERSION=0.12.17

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS UV

### BUILDER

FROM python:${PYTHON_VER}-${IMG_OPTION} AS BUILDER

COPY --from=UV /uv /uvx /bin/

WORKDIR /local
COPY . /local

ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN apk add --no-cache build-base # Add build-base package
RUN uv sync --locked --no-dev --extra cli --no-editable

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
        "org.opencontainers.image.source"="https://github.com/aristanetworks/anta" \
        "org.opencontainers.image.url"="https://anta.arista.com" \
        "org.opencontainers.image.documentation"="https://anta.arista.com" \
        "org.opencontainers.image.licenses"="Apache-2.0" \
        "org.opencontainers.image.vendor"="Arista Networks" \
        "org.opencontainers.image.authors"="Khelil Sator, Angélique Phillipps, Colin MacGiollaEáin, Matthieu Tache, Onur Gashi, Paul Lavelle, Guillaume Mulocher, Thomas Grimonet" \
        "org.opencontainers.image.base.name"="python" \
        "org.opencontainers.image.revision"="dev" \
        "org.opencontainers.image.version"="dev"

# Copy artifacts from builder
COPY --from=BUILDER /opt/venv /opt/venv

# Define PATH and default user
ENV PATH="/opt/venv/bin:$PATH"

USER anta

ENTRYPOINT [ "/opt/venv/bin/anta" ]
