# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= --write-all --fresh-env
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
PKG           = ../configparser_override

# Put it first so that "make" without argument is like "make help".
.PHONY: help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: livehtml
livehtml:
	sphinx-autobuild -b html --open-browser --port 9000 --watch $(PKG) -c . $(SOURCEDIR) $(BUILDDIR)/html

.PHONY: apidocs
apidocs:
	sphinx-apidoc --maxdepth 2 --remove-old --force --module-first --separate --output-dir $(SOURCEDIR)/api $(PKG)

.PHONY: clean
clean:
	rm -rf ./_build
	rm -rf ./api

.PHONY: build
build: apidocs html
	@echo "$@"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: Makefile
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
