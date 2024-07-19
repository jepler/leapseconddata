.. SPDX-FileCopyrightText: 2021 Jeff Epler
.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

leapseconddata |version|
========================

.. image:: https://github.com/jepler/leapseconddata/actions/workflows/test.yml/badge.svg
    :target: https://github.com/jepler/leapseconddata/actions/workflows/test.yml
    :alt: Test leapseconddata

.. image:: https://img.shields.io/pypi/v/leapseconddata
    :target: https://pypi.org/project/leapseconddata
    :alt: PyPI

This module allows you to download and extract leap second data from
various trusted sources, both offline and online, in order to:

* Convert dates and times between TAI and UTC;
* Determine if a date has an extra second at the end in UTC.

You can also find the project in the following locations:

* `jelper/leapseconddata repository on Github
  <https://github.com/jepler/leapseconddata>`_;
* `leapseconddata project on PyPI
  <https://pypi.org/project/leapseconddata/>`_.

The project’s code and documentation contents are licensed under GNU General
Public License version 3.

How-to guides
-------------

These sections provide guides, i.e. recipes, targeted towards various actors.
They guide you through the steps involved in addressing key problems
and use-cases.

.. toctree::
    :maxdepth: 3

    guides
    developer-guides

Discussion topics
-----------------

These sections discuss key topics and concepts at a fairly high level, and
provide useful background information and explanation.

.. toctree::
    :maxdepth: 3

    topics

References
----------

These sections provide technical reference for APIs and other aspects of
the project's machinery. They go into detail, and therefore, assume you
have a basic understanding of key concepts.

.. toctree::
    :maxdepth: 2

    code
