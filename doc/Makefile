# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS?=
SPHINXBUILD?=sphinx-build
SOURCEDIR=source
SPHINXAPIDIR=autoapi
BUILDDIR=build

export EOS_SITE_NAME?=test-gemdaq-ci
export EOS_SITE_PATH?=/tmp/$(USER)/$(EOS_SITE_NAME)
export EOS_SITE_URL?=https://$(EOS_SITE_NAME).web.cern.ch/$(EOS_SITE_NAME)
export GEM_DOCS_URL?=$(EOS_SITE_URL)

export PYTHONSOURCE=$(shell dirname `pwd`)/pkg

ENV_NAME?=docs
CONDA_ENV_FILE?=/etc/profile.d/conda.sh
CONDA_DIR=/tmp/$(USER)/conda
CONDA_RUN=conda run -n $(ENV_NAME)
ifdef USE_CONDA
CONDA_EXE=. $(CONDA_ENV_FILE) && $(CONDA_RUN)
else
$(warning "Please ensure that the envronment from which make has been called is configured with the proper packages, as specified in the requirements.txt file")
CONDA_EXE=
endif
CONDA_PY_VER?=2.7

.PHONY: help Makefile

# Put it first so that "make" without argument is like "make help".
help:
	@$(CONDA_EXE) $(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: docs
docs: html

.PHONY: deploy
deploy: docs
	find $(BUILD_DIR)/html -type f -iname '*.html' -print0 -exec \
		perl -pi -e "s|SITE_ROOT|$(EOS_SITE_NAME)|g" {} \+
	find $(BUILD_DIR)/html -type f -iname '*.html' -print0 -exec \
		perl -pi -e "s|http://0.0.0.0:8000/|/|g" {} \+
	find $(BUILD_DIR)/html -type f -iname '*.html' -print0 -exec \
		perl -pi -e "s|http://0.0.0.0:8000|/|g" {} \+

condasetup.$(ENV_NAME).env:
	. $(CONDA_ENV_FILE) && \
	conda config --append envs_dirs $(CONDA_DIR) && \
	conda create -p $(CONDA_DIR)/$(ENV_NAME) python=$(CONDA_PY_VER) -y && \
	$(CONDA_RUN) python -m pip install -r requirements.txt && \
	touch $@

.PHONY: cleanapi cleanconda
cleanapi:
	rm -rf $(SOURCEDIR)/$(SPHINXAPIDIR)

cleanconda:
	rm -rf $(CONDA_DIR)/$(ENV_NAME)
	rm -rf condasetup.$(ENV_NAME).env

.PHONY: clean cleanall
clean:
	rm -rf $(BUILDDIR)

cleanall: clean cleanapi

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
%:
	@$(CONDA_EXE) $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

ifdef USE_CONDA
help html man: | condasetup.$(ENV_NAME).env
## this doesn't work
#%: condasetup.$(ENV_NAME).env
## this forces condasetup to run even in no-op mode, but it solves the other problem...
#Makefile: | condasetup.$(ENV_NAME).env
endif
