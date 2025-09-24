include ../.devcontainer/tools.mk

ESBONIO ?= --pre esbonio

export PATH := $(BIN):$(PATH)

.PHONY: clean
clean:
	rm -r bundled node_modules dist

.PHONY: test
test: dev-deps | $(NPM)
	-test -d dist && rm -r dist
	$(NPX) tsc -p .
	$(NPM) run test

.PHONY: watch
watch: dev-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run watch

.PHONY: compile
compile: dev-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run compile

.PHONY: install
install: compile
	-test -d ../.vscode/extensions || mkdir -p ../.vscode/extensions
	test -L ../.vscode/extensions/esbonio || ln -s $(PWD) ../.vscode/extensions/esbonio

.PHONY: dist
dist: release-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run package

.PHONY: release
release: $(TOWNCRIER) $(HATCH) $(PY)
	$(PY) ../scripts/make_release.py lsp
	$(PY) ../scripts/make_release.py vscode

# Ensures the version of esbonio in ../lib/esbonio is used.
.PHONY: dev-deps
dev-deps: node_modules/.installed bundled/libs/.installed bundled/env/.installed
	-test -d bundled/libs/esbonio-*.dist-info  && rm -r bundled/libs/esbonio-*.dist-info
	-test -L bundled/libs/esbonio  || rm -r bundled/libs/esbonio
	if [ ! -f bundled/libs/esbonio/__main__.py ]; then \
	  test -L bundled/libs/esbonio && rm bundled/libs/esbonio; \
	  ln -s $(shell pwd)/../lib/esbonio/esbonio bundled/libs/esbonio; \
	fi

# Ensures the latest version of esbonio from PyPi is used.
.PHONY: release-deps
release-deps: node_modules/.installed bundled/libs/.installed bundled/env/.installed
	-test -L bundled/libs/esbonio && rm bundled/libs/esbonio
	test -d bundled/libs/esbonio-*.dist-info || $(PY310) -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade $(ESBONIO)

# Generic rule for converting requirements-*.in to requirements-*.txt
%.txt: %.in | $(UV)
	$(UV) pip compile --prerelease=allow --generate-hashes --upgrade --python-version 3.10 --output-file $@ $<

# Can't use uv for installation until --implementation py is supported
# https://github.com/astral-sh/uv/issues/6246
bundled/libs/.installed: requirements-libs.txt | $(PY310)
	-test -d bundled/libs  && rm -r bundled/libs
	$(PY310) --version
	$(PY310) -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements-libs.txt
	touch $@

bundled/env/.installed: requirements-env.txt | $(PY310)
	-test -d bundled/env  && rm -r bundled/env
	$(PY310) --version
	$(PY310) -m pip install -t ./bundled/env --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements-env.txt
	touch $@

node_modules/.installed: package.json package-lock.json | $(NPM)
	$(NPM) ci
	touch $@
