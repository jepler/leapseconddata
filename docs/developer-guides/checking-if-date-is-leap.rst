.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

Checking if a date has a leap second
====================================

In order to check if a date has a leap second, you must first
obtain the leap second data by using one of the methods described
in :ref:`devguide-obtaining-leaps`. Then, you can iterate over
the fetched leap seconds to check for the date.

For example, in order to check if December 31st, 2016 has a leap
second, you can use the following code:

.. literalinclude:: check-date-leap.py

The output of this program is the following:

.. literalinclude:: check-date-leap.py.exp
