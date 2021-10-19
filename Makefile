PYTHON ?= python3

.PHONY: all
all: coverage mypy

COVERAGE_INCLUDE=--omit '/usr/**/*.py'
.PHONY: coverage
coverage:
	$(PYTHON) -mcoverage run --branch -m unittest leapseconddata_test.py
	$(PYTHON) -mcoverage html $(COVERAGE_INCLUDE)
	$(PYTHON) -mcoverage report $(COVERAGE_INCLUDE) --fail-under=100

.PHONY: mypy
mypy:
	mypy --strict *.py
# Copyright (C) 2021 Jeff Epler <jepler@gmail.com>
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only
