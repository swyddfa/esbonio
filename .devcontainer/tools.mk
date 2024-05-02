BIN ?= $(HOME)/.local/bin

PY38 ?= $(or $(shell command -v python3.8), $(BIN)/python3.8)
PY39 ?= $(or $(shell command -v python3.9), $(BIN)/python3.9)
PY310 ?= $(or $(shell command -v python3.10), $(BIN)/python3.10)
PY311 ?= $(or $(shell command -v python3.11), $(BIN)/python3.11)
PY312 ?= $(or $(shell command -v python3.12), $(BIN)/python3.12)

# Set a default python
PY ?= $(or $(shell command -v python), $(BIN)/python)
PY_INTERPRETERS := $(PY) $(PY38) $(PY39) $(PY310) $(PY311) $(PY312)

HATCH ?= $(or $(shell command -v hatch), $(BIN)/hatch)
HATCH_VERSION = 1.9.7
PRE_COMMIT ?= $(or $(shell command -v pre-commit), $(BIN)/pre-commit)
TOWNCRIER ?= $(or $(shell command -v towncrier), $(BIN)/towncrier)

PY_TOOLS := $(HATCH) $(PRE_COMMIT) $(TOWNCRIER)

# Node JS
NPM ?= $(or $(shell command -v npm), $(BIN)/npm)
NODE ?= $(or $(shell command -v node), $(BIN)/node)
NODE_VERSION := 18.20.2
NODE_DIR := $(HOME)/.local/node

tools: $(PY_INTERPRETERS) $(PY_TOOLS) $(NPM) $(NODE)
	for prog in $^ ; do echo -n "$${prog}\t" ; $${prog} --version; done

$(HATCH):
	curl -L --output /tmp/hatch.tar.gz https://github.com/pypa/hatch/releases/download/hatch-v$(HATCH_VERSION)/hatch-$(HATCH_VERSION)-x86_64-unknown-linux-gnu.tar.gz
	tar -xf /tmp/hatch.tar.gz -C /tmp
	rm /tmp/hatch.tar.gz

	[ -d $(BIN) ] || mkdir -p $(BIN)
	mv /tmp/hatch-$(HATCH_VERSION)-x86_64-unknown-linux-gnu $(HATCH)

	$@ --version
	touch $@

$(PY38): $(HATCH)
	$(HATCH) python find 3.8  || $(HATCH) python install 3.8
	ln -s $$($(HATCH) python find 3.8) $@

	$@ --version
	touch $@

$(PY39): $(HATCH)
	$(HATCH) python find 3.9  || $(HATCH) python install 3.9
	ln -s $$($(HATCH) python find 3.9) $@

	$@ --version
	touch $@

$(PY310): $(HATCH)
	$(HATCH) python find 3.10  || $(HATCH) python install 3.10
	ln -s $$($(HATCH) python find 3.10) $@

	$@ --version
	touch $@

$(PY311): $(HATCH)
	$(HATCH) python find 3.11  || $(HATCH) python install 3.11
	ln -s $$($(HATCH) python find 3.11) $@

	$@ --version
	touch $@

$(PY312): $(HATCH)
	$(HATCH) python find 3.12  || $(HATCH) python install 3.12
	ln -s $$($(HATCH) python find 3.12) $@

	$@ --version
	touch $@

$(PY): $(PY312)
	ln -s $< $@
	$@ --version
	touch $@

$(PRE_COMMIT): $(PY)
	$(PY) -m pip install --user pre-commit
	$@ --version
	touch $@

$(TOWNCRIER): $(PY)
	$(PY) -m pip install --user towncrier
	$@ --version
	touch $@

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
