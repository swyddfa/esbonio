FROM mcr.microsoft.com/devcontainers/base:jammy

# Extra dependencies needed to run headless VSCode tests
RUN apt update && apt install -y libasound2 \
                               libatk1.0-0 \
                               libatk-bridge2.0-0 \
                               libcairo2 \
                               libdbus-1-3 \
                               libgbm1 \
                               libglib2.0-0 \
                               libgtk-3-0 \
                               libnspr4 \
                               libnss3 \
                               xvfb \
               && rm -rf /var/lib/apt/lists/*

COPY tools.mk /

RUN su vscode -c "make -f tools.mk tools" \
    && rm tools.mk
