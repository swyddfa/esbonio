FROM mcr.microsoft.com/devcontainers/base:jammy

COPY tools.mk /

RUN su vscode -c "make -f tools.mk tools" \
    && rm tools.mk
