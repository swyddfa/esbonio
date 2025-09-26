include .devcontainer/tools.mk

.PHONY: lint
lint: $(UVX)
	$(UVX) pre-commit run --all-files

.PHONY: enable-pre-commit
enable-pre-commit: $(UVX)
	$(UVX) pre-commit install

.PHONY: disable-pre-commit
disable-pre-commit: $(UVX)
	$(UVX) pre-commit uninstall
