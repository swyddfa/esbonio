ARCH ?= $(shell arch)
BIN ?= $(HOME)/.local/bin

ifeq ($(strip $(ARCH)),)
$(error Unable to determine platform architecture)
endif

NODE_VERSION := 20.18.0
PY_VERSION := 3.13
UV_VERSION := 0.5.21

UV ?= $(shell command -v uv)
UVX ?= $(shell command -v uvx)

ifeq ($(strip $(UV)),)

UV := $(BIN)/uv
UVX := $(BIN)/uvx

$(UV):
	curl -L --output /tmp/uv.tar.gz https://github.com/astral-sh/uv/releases/download/$(UV_VERSION)/uv-$(ARCH)-unknown-linux-gnu.tar.gz
	tar -xf /tmp/uv.tar.gz -C /tmp
	rm /tmp/uv.tar.gz

	test -d $(BIN) || mkdir -p $(BIN)

	mv /tmp/uv-$(ARCH)-unknown-linux-gnu/uv $@
	mv /tmp/uv-$(ARCH)-unknown-linux-gnu/uvx $(UVX)

	$@ --version
	$(UVX) --version

endif


# Hatch is not only used for building packages, but bootstrapping any missing
# interpreters
HATCH ?= $(shell command -v hatch)

ifeq ($(strip $(HATCH)),)

HATCH := $(BIN)/hatch

$(HATCH): | $(UV)
	$(UV) tool install hatch
	$@ --version

endif

PRE_COMMIT ?= $(shell command -v pre-commit)

ifeq ($(strip $(PRE_COMMIT)),)
PRE_COMMIT := $(BIN)/pre-commit

$(PRE_COMMIT): | $(UV)
	$(UV) tool install pre-commit
	$@ --version

endif

PY_TOOLS := $(HATCH) $(PRE_COMMIT)

# Set a default `python` command if there is not one already
PY ?= $(shell command -v python)

ifeq ($(strip $(PY)),)
PY := $(BIN)/python

$(PY): | $(UV)
	$(UV) python install $(PY_VERSION)
	ln -s $$($(UV) python find $(PY_VERSION)) $@
	$@ --version
endif

# Node JS
NPM ?= $(shell command -v npm)

ifeq ($(strip $(NPM)),)

NPM := $(BIN)/npm
NODE := $(BIN)/node
NODE_DIR := $(HOME)/.local/node

$(NPM):
	curl -L --output /tmp/node.tar.xz https://nodejs.org/dist/v$(NODE_VERSION)/node-v$(NODE_VERSION)-linux-x64.tar.xz
	tar -xJf /tmp/node.tar.xz -C /tmp
	rm /tmp/node.tar.xz

	[ -d $(NODE_DIR) ] || mkdir -p $(NODE_DIR)
	mv /tmp/node-v$(NODE_VERSION)-linux-x64/* $(NODE_DIR)

	[ -d $(BIN) ] || mkdir -p $(BIN)
	ln -s $(NODE_DIR)/bin/node $(NODE)
	ln -s $(NODE_DIR)/bin/npm $(NPM)

	$(NODE) --version
	PATH=$(BIN) $(NPM) --version

endif

# One command to bootstrap all tools and check their versions
tools: $(PY) $(PY_TOOLS) $(NPM)
	for prog in $^ ; do echo -n "$${prog}\t" ; PATH=$(BIN) $${prog} --version; done
