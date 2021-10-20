PYTHON ?= python3

.PHONY: all
all: coverage mypy

COVERAGE_INCLUDE=--omit '/usr/**/*.py'
.PHONY: coverage
coverage:
	$(PYTHON) -mcoverage run --branch -m unittest testleapseconddata.py
	$(PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage report $(COVERAGE_INCLUDE) --fail-under=100

.PHONY: mypy
mypy:
	mypy --strict *.py

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= -a -E -j auto
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
.PHONY: help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# Route particular targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: html
html:
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
