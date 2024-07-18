.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

Converting a UTC date and time to TAI
=====================================

.. py:currentmodule:: leapseconddata

In order to convert a UTC date and time to TAI, you must first
obtain the leap second data by using one of the methods described
in :ref:`devguide-obtaining-leaps`. Then, you can use the
:py:meth:`LeapSecondData.to_tai` method to convert the date and time.

For example:

.. literalinclude:: convert-utc-to-tai.py

This program will provide you with the following output:

.. code-block:: text

    2024-07-18T22:00:37+00:00
