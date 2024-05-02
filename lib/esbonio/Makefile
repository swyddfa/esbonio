include ../../.devcontainer/tools.mk

.PHONY: dist

dist: $(HATCH)
	$(HATCH) build

release: $(TOWNCRIER) $(HATCH) $(PY)
	$(PY) ../scripts/make_release.py lsp
