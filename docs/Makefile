ifeq ($(CI),true)
	BUILD=html-build
else
	BUILD=html-local
endif


ifeq ($(GITHUB_REF),refs/heads/release)
	BUILDDIR=stable
else ifeq ($(GITHUB_REF),refs/heads/beta)
	BUILDDIR=beta
else
	BUILDDIR=latest
endif


html-build:
	BUILDDIR=$(BUILDDIR) sphinx-build -b html . _build/$(BUILDDIR)/en/
	BUILDDIR=$(BUILDDIR) sphinx-build -b html . _build/$(BUILDDIR)/cy/ -Dlanguage=cy
	echo "version=$(BUILDDIR)" >> $(GITHUB_OUTPUT)

html-local:
	sphinx-build -M html . _build $(SPHINXOPTS)

html: $(BUILD)
