include ../.devcontainer/tools.mk

SPHINX_OPTS ?=
BUILDDIR ?=_build

default: html

.PHONY: clean
clean:
	rm -r _build

html: $(HATCH)
	$(HATCH) -e docs run sphinx-build -- -M dirhtml . $(BUILDDIR) $(SPHINX_OPTS)
