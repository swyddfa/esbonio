ARCH ?= $(shell arch)
BIN ?= $(HOME)/.local/bin

ifeq ($(strip $(ARCH)),)
$(error Unable to determine platform architecture)
endif

HATCH_VERSION = 1.10.0
NODE_VERSION := 18.20.2

# The versions of Python we support
PYXX_versions := 3.8 3.9 3.10 3.11 3.12
PY_INTERPRETERS =

# Hatch is not only used for building packages, but bootstrapping any missing
# interpreters
HATCH ?= $(or $(shell command -v hatch), $(BIN)/hatch)

$(HATCH):
	curl -L --output /tmp/hatch.tar.gz https://github.com/pypa/hatch/releases/download/hatch-v$(HATCH_VERSION)/hatch-$(HATCH_VERSION)-$(ARCH)-unknown-linux-gnu.tar.gz
	tar -xf /tmp/hatch.tar.gz -C /tmp
	rm /tmp/hatch.tar.gz

	test -d $(BIN) || mkdir -p $(BIN)
	mv /tmp/hatch-$(HATCH_VERSION)-$(ARCH)-unknown-linux-gnu $(HATCH)

	$@ --version
	touch $@

# This effectively defines a function `PYXX` that takes a Python version number
# (e.g. 3.8) and expands it out into a common block of code that will ensure a
# verison of that interpreter is available to be used.
#
# The is perhaps a bit more complicated than I'd like, but it should mean that
# the project's makefiles are useful both inside and outside of a devcontainer.
#
# `PYXX` has the following behavior:
# - If possible, it will reuse the user's existing version of Python
#   i.e. $(shell command -v pythonX.X)
#
# - The user may force a specific interpreter to be used by setting the
#   variable when running make e.g. PYXX=/path/to/pythonX.X make ...
#
# - Otherwise, `make` will use `$(HATCH)` to install the given version of
#   Python under `$(BIN)`
#
# See: https://www.gnu.org/software/make/manual/html_node/Eval-Function.html
define PYXX =

PY$(subst .,,$1) ?= $$(shell command -v python$1)

ifeq ($$(strip $$(PY$(subst .,,$1))),)

PY$(subst .,,$1) := $$(BIN)/python$1

$$(PY$(subst .,,$1)): $$(HATCH)
	$$(HATCH) python find $1 || $$(HATCH) python install $1
	ln -s $$$$($$(HATCH) python find $1) $$@

	$$@ --version
	touch $$@

endif

PY_INTERPRETERS += $$(PY$(subst .,,$1))
endef

# Uncomment the following line to see what this expands into.
#$(foreach version,$(PYXX_versions),$(info $(call PYXX,$(version))))
$(foreach version,$(PYXX_versions),$(eval $(call PYXX,$(version))))

# Set a default `python` command if there is not one already
PY ?= $(shell command -v python)

ifeq ($(strip $(PY)),)
PY := $(BIN)/python

$(PY): $(PY312)
	ln -s $< $@
	$@ --version
	touch $@
endif

PY_INTERPRETERS += $(PY)
#$(info $(PY_INTERPRETERS))

PRE_COMMIT ?= $(shell command -v pre-commit)

ifeq ($(strip $(PRE_COMMIT)),)
PRE_COMMIT := $(BIN)/pre-commit

$(PRE_COMMIT): $(PY)
	$(PY) -m pip install --user pre-commit
	$@ --version
	touch $@
endif

PY_TOOLS := $(HATCH) $(PRE_COMMIT)

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
tools: $(PY_INTERPRETERS) $(PY_TOOLS) $(NPM)
	for prog in $^ ; do echo -n "$${prog}\t" ; PATH=$(BIN) $${prog} --version; done
