PY ?= 310

.PHONY: develop test

develop:
	nix develop .#py$(PY)

test:
	nix develop .#py$(PY) --command pytest
