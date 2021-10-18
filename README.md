<!--
SPDX-FileCopyrightText: 2021 Jeff Epler

SPDX-License-Identifier: GPL-3.0-only
-->

# Python Leap Second List

Leap seconds are corrections applied irregularly so that the UTC day stays
fixed to the earth's rotation.

This module provides a class for parsing and validating the standard
`leap-seconds.list` file.  Once parsed, it is possible to retrieve the
full list of leap seconds, or find the TAI-UTC offset for any UTC time.
