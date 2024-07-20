.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

Converting a TAI date and time to UTC
=====================================

.. py:currentmodule:: leapseconddata

In order to convert a TAI date and time to UTC, you must first
obtain the leap second data by using one of the methods described
in :ref:`devguide-obtaining-leaps`. Then, you can use the
:py:meth:`LeapSecondData.tai_to_utc` method to convert the date and time.

For example:

.. literalinclude:: convert-tai-to-utc.py

This program will provide you with the following output:

.. literalinclude:: convert-tai-to-utc.py.exp
