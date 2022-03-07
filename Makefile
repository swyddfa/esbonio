.PHONY: preview-completion-docs completion-docs venv npm

VENV := .env

ifeq ($(CI),true)
	PYTHON=python
endif

# Default python env.
ifndef PYTHON
	PYTHON=$(VENV)/bin/python
endif

# ---------------------------------------- Development Environments -------------------------------------------
$(VENV)/bin/python:
	python3 -m venv $(VENV)
	$@ -m pip install --upgrade pip
	$@ -m pip install -r docs/requirements.txt
	$@ -m pip install -e lib/esbonio[dev]
	$@ -m pip install -e lib/esbonio-extensions[dev]

venv: $(VENV)/bin/python

code/node_modules: code/package.json code/package-lock.json
	npm --prefix ./code/ install

npm: code/node_modules

# ---------------------------------------- Tests, Lints, Tools etc. -------------------------------------------
mypy: $(PYTHON)
	mypy --namespace-packages --explicit-package-bases -p esbonio

# ---------------------------------------- CompletionItem Documentation ---------------------------------------
DOCUTILS_COMPLETION_DOCS=lib/esbonio/esbonio/lsp/rst/roles.json lib/esbonio/esbonio/lsp/rst/directives.json
SPHINX_COMPLETION_DOCS=lib/esbonio/esbonio/lsp/sphinx/roles.json lib/esbonio/esbonio/lsp/sphinx/directives.json
COMPLETION_DOCS=$(SPHINX_COMPLETION_DOCS) $(DOCUTILS_COMPLETION_DOCS)

# '&:' Indicates that the multiple targets listed are 'grouped' and that they are produced together from running
#      the command below once. This prevents the command being run once for each file produced.
#      https://www.gnu.org/software/make/manual/html_node/Multiple-Targets.html
#
# '$^' Expands into the list of dependencies of the target (python .... in this case)
#      https://www.gnu.org/software/make/manual/html_node/Automatic-Variables.html#Automatic-Variables
$(DOCUTILS_COMPLETION_DOCS) &: $(PYTHON) scripts/generate_docutils_documentation.py
	$^ -o lib/esbonio/esbonio/lsp/rst/

$(SPHINX_COMPLETION_DOCS) &: $(PYTHON) scripts/generate_sphinx_documentation.py
	$^ -o lib/esbonio/esbonio/lsp/sphinx/

completion-docs: $(COMPLETION_DOCS)

preview-completion-docs: $(COMPLETION_DOCS)
	$(PYTHON) scripts/preview_documentation.py $(COMPLETION_DOCS)
