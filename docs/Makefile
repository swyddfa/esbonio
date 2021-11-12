
ifeq ($(CI),true)
	BUILD=html-build
else
	BUILD=html-local
endif


ifeq ($(GITHUB_REF),refs/heads/release)
	BUILDDIR=stable
else
	BUILDDIR=latest
endif


html-build:
	sphinx-build -b html . _build/$(BUILDDIR)/en/
	sphinx-build -b html . _build/$(BUILDDIR)/cy/ -Dlanguage=cy
	echo "::set-output name=version::$(BUILDDIR)"


html-local:
	sphinx-build -M html . _build $(SPHINXOPTS)

html: $(BUILD)
