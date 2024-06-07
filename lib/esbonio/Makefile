include ../../.devcontainer/tools.mk


# Global flags to pass to hatch, e.g. -v, --no-color etc.
HATCH_ARGS =

.PHONY: dist release test

dist: $(HATCH)
	$(HATCH) $(HATCH_ARGS) build

test: ARGS ?= -i py=$(shell $(PY) -c 'import sys;v=sys.version_info;print(f"{v.major}.{v.minor}")')
test: $(HATCH) $(PY)
	$(HATCH) $(HATCH_ARGS) test $(ARGS)

release: $(TOWNCRIER) $(HATCH) $(PY)
	$(PY) ../scripts/make_release.py lsp
