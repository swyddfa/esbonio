include ../.devcontainer/tools.mk

ESBONIO ?= --pre esbonio

.PHONY: dist dev-deps release-deps

watch: dev-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run watch

compile: dev-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run compile

dist: release-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run package

# Ensures the version of esbonio in ../lib/esbonio is used.
dev-deps: node_modules/.installed bundled/libs/.installed
	-test -d bundled/libs/esbonio-*.dist-info  && rm -r bundled/libs/esbonio-*.dist-info
	-test -L bundled/libs/esbonio  || rm -r bundled/libs/esbonio
	if [ ! -f bundled/libs/esbonio/__main__.py ]; then \
	  test -L bundled/libs/esbonio && rm bundled/libs/esbonio; \
	  ln -s $(shell pwd)/../lib/esbonio/esbonio bundled/libs/esbonio; \
	fi

# Ensures the latest version of esbonio from PyPi is used.
release-deps: node_modules/.installed bundled/libs/.installed
	-test -L bundled/libs/esbonio && rm bundled/libs/esbonio
	test -d bundled/libs/esbonio-*.dist-info || $(PY38) -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade $(ESBONIO)

requirements.txt: $(HATCH) requirements.in
	$(HATCH) run deps:update

bundled/libs/.installed: $(PY38) requirements.txt
	-test -d bundled/libs  && rm -r bundled/libs
	$(PY38) --version
	$(PY38) -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements.txt
	touch $@

node_modules/.installed: package.json package-lock.json $(NPM)
	$(NPM) ci
	touch $@
