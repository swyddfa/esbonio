FROM mcr.microsoft.com/devcontainers/base:jammy

COPY tools.mk /

RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3-venv \
    && su vscode -c "make -f tools.mk tools" \
    && rm tools.mk
