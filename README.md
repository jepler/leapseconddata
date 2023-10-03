<!--
SPDX-FileCopyrightText: 2021 Jeff Epler

SPDX-License-Identifier: GPL-3.0-only
-->
[![Test leapseconddata](https://github.com/jepler/leapseconddata/actions/workflows/test.yml/badge.svg)](https://github.com/jepler/leapseconddata/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/leapseconddata)](https://pypi.org/project/leapseconddata)
[![Documentation Status](https://readthedocs.org/projects/leapseconddata/badge/?version=latest)](https://leapseconddata.readthedocs.io/en/latest/?badge=latest)

# Python Leap Second List

Leap seconds are corrections applied irregularly so that the UTC day stays
fixed to the earth's rotation.

This module provides a class for parsing and validating the standard
`leap-seconds.list` file.  Once parsed, it is possible to retrieve the
full list of leap seconds, or find the TAI-UTC offset for any UTC time.
