include ../../.devcontainer/tools.mk


# Global flags to pass to hatch, e.g. -v, --no-color etc.
HATCH_ARGS =

.PHONY: clean-env
clean-env: | $(HATCH)
	for venv in $$($(HATCH) env show -i --json | jq -r 'keys | join(" ")') ; do $(HATCH) env remove "$${venv}" ; done

.PHONY: dist
dist: $(HATCH)
	$(HATCH) $(HATCH_ARGS) build


.PHONY: lint
lint: | $(UVX)
	$(UVX) pre-commit run --all-files $(HOOK)

.PHONY: test
test: ARGS ?= -i py=$(shell $(PY) -c 'import sys;v=sys.version_info;print(f"{v.major}.{v.minor}")')
test: $(HATCH) $(PY)
	$(HATCH) $(HATCH_ARGS) test $(ARGS)


.PHONY: release
release: $(TOWNCRIER) $(HATCH) $(PY)
	$(PY) ../scripts/make_release.py lsp
