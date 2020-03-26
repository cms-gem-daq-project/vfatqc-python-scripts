# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS?=
SPHINXBUILD?=sphinx-build
SPHINXAPIBUILD?=sphinx-apidoc
SOURCEDIR=source
BUILDDIR=build

EOS_SITE_NAME?=test-gemdaq-ci
EOS_SITE_PATH?=/tmp/$(USER)/$(EOS_SITE_NAME)

export EOS_SITE_URL?=https://$(EOS_SITE_NAME).web.cern.ch/$(EOS_SITE_NAME)
export GEM_DOCS_URL?=$(EOS_SITE_URL)

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: autoapi
autoapi:
	$(SPHINXAPIBUILD) -M -o "$(SOURCEDIR)/sphinx-api" ../pkg/gempython

.PHONY: cleanapi
cleanapi:
	rm -rf source/sphinx-api

.PHONY: docs
docs: html

.PHONY: clean cleanall help Makefile
clean:
	rm -rf build

cleanall: clean cleanapi

html: autoapi

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
