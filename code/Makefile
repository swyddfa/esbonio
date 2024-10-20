include ../.devcontainer/tools.mk

ESBONIO ?= --pre esbonio

.PHONY: dist dev-deps release-deps release install

watch: dev-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run watch

compile: dev-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run compile

install: compile
	-test -d ../.vscode/extensions || mkdir -p ../.vscode/extensions
	test -L ../.vscode/extensions/esbonio || ln -s $(PWD) ../.vscode/extensions/esbonio

dist: release-deps $(NPM)
	-test -d dist && rm -r dist
	$(NPM) run package

release: $(TOWNCRIER) $(HATCH) $(PY)
	$(PY) ../scripts/make_release.py lsp
	$(PY) ../scripts/make_release.py vscode

# Ensures the version of esbonio in ../lib/esbonio is used.
dev-deps: node_modules/.installed bundled/libs/.installed bundled/env/.installed
	-test -d bundled/libs/esbonio-*.dist-info  && rm -r bundled/libs/esbonio-*.dist-info
	-test -L bundled/libs/esbonio  || rm -r bundled/libs/esbonio
	if [ ! -f bundled/libs/esbonio/__main__.py ]; then \
	  test -L bundled/libs/esbonio && rm bundled/libs/esbonio; \
	  ln -s $(shell pwd)/../lib/esbonio/esbonio bundled/libs/esbonio; \
	fi

# Ensures the latest version of esbonio from PyPi is used.
release-deps: node_modules/.installed bundled/libs/.installed bundled/env/.installed
	-test -L bundled/libs/esbonio && rm bundled/libs/esbonio
	test -d bundled/libs/esbonio-*.dist-info || $(PY39) -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade $(ESBONIO)

# Hatch is only required to exist, don't rebuild this target if it happens to be newer!
# https://www.gnu.org/software/make/manual/html_node/Prerequisite-Types.html
requirements-libs.txt: requirements-libs.in | $(HATCH)
	$(HATCH) run deps:update-libs

requirements-env.txt: requirements-env.in | $(HATCH)
	$(HATCH) run deps:update-env

bundled/libs/.installed: $(PY39) requirements-libs.txt
	-test -d bundled/libs  && rm -r bundled/libs
	$(PY39) --version
	$(PY39) -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements-libs.txt
	touch $@

bundled/env/.installed: $(PY39) requirements-env.txt
	-test -d bundled/env  && rm -r bundled/env
	$(PY39) --version
	$(PY39) -m pip install -t ./bundled/env --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements-env.txt
	touch $@

node_modules/.installed: package.json package-lock.json $(NPM)
	$(NPM) ci
	touch $@
