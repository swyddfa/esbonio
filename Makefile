include .devcontainer/tools.mk

.PHONY: lint enable-pre-commit disable-pre-commit

lint: $(PRE_COMMIT)
	$(PRE_COMMIT) run --all-files


enable-pre-commit: $(PRE_COMMIT)
	$(PRE_COMMIT) install

disable-pre-commit: $(PRE_COMMIT)
	$(PRE_COMMIT) uninstall
