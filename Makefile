VENV_BIN = _env/bin
VENV_PYTHON = $(VENV_BIN)/python3

.PHONY: all
all: coverage mypy

COVERAGE_INCLUDE=--omit '/usr/**/*.py'
.PHONY: coverage
coverage: $(VENV_PYTHON)
	$(VENV_PYTHON) -mcoverage run --branch -m unittest testleapseconddata.py
	$(VENV_PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(VENV_PYTHON) -mcoverage report $(COVERAGE_INCLUDE) --fail-under=100

.PHONY: mypy
mypy: $(VENV_PYTHON)
	$(VENV_BIN)/mypy --strict leapseconddata testleapseconddata.py

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= -a -E -j auto
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
.PHONY: help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# Route particular targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: html
html: $(VENV_PYTHON)
	@$(VENV_PYHTON) $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

$(VENV_PYTHON):
	python -mvenv _env
	_env/bin/pip install -r requirements-dev.txt

# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
