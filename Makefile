PYTHON ?= python3

.PHONY: all
all: coverage mypy

COVERAGE_INCLUDE=--omit '/usr/**/*.py'
.PHONY: coverage
coverage:
	$(PYTHON) -mcoverage run --branch -m leapseconddata
	$(PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage annotate $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage report $(COVERAGE_INCLUDE)

.PHONY: mypy
mypy:
	mypy --strict leapseconddata.py
# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
