include ../.devcontainer/tools.mk

SPHINX_OPTS ?=
BUILDDIR ?=_build

default: html

.PHONY: clean-env
clean-env: | $(HATCH)
	for venv in $$($(HATCH) env show -i --json | jq -r 'keys | join(" ")') ; do $(HATCH) env remove "$${venv}" ; done

.PHONY: clean
clean:
	rm -r _build

html: | $(HATCH)
	$(HATCH) -e docs run sphinx-build -- -M dirhtml . $(BUILDDIR) $(SPHINX_OPTS)
