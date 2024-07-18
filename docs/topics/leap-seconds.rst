.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

What are leap seconds?
======================

`Coordinated Universal Time (UTC) <UTC_>`_ is a time standard based on two
other standards, `International Atomic Time (TAI) <TAI_>`_ and
`Universal Time (UT1) <UT1_>`_. It aims at being at a whole second offset
from TAI, while keeping UTC and UT1 within 0.9 seconds of each other.

In order to accomplish that, UTC bases itself on TAI, and gets `leap seconds`_
added to it when considered necessary by the `International Earth Rotation
Service (IERS) <IERS_>`_, in a semi-annually published bulletin called
`Bulletin C`_ which announces whether or not a leap second is inserted
in June 30th and/or December 31st, meaning the UTC clock may reach ``23:59:60``
on these dates.

.. note::

    With timezones, the leap second may not be inserted at ``23:59``, but
    at another time. For example:

    * In France, using Central European Time (CET, UTC+01:00), the leap second
      was inserted on January 1st, 2017, at ``00:59:60``.
    * In Australia, using Australian Western Central Standard Time (AWCST,
      UTC+08:45), the leap second was inserted on January 1st, 2017,
      at ``08:44:60``.
    * In the United States, using Mountain Time Zone (UTC-07:00), the leap
      second was inserted on December 31st, 2016, at ``16:59:60``.

For more information, you can read `The Unix leap second mess (madore.org)
<http://www.madore.org/%7Edavid/computers/unix-leap-seconds.html>`_, as
well as the Wikipedia pages linked above.

.. _UTC: https://en.wikipedia.org/wiki/Coordinated_Universal_Time
.. _TAI: https://en.wikipedia.org/wiki/International_Atomic_Time
.. _UT1: https://en.wikipedia.org/wiki/Universal_Time
.. _leap seconds: https://en.wikipedia.org/wiki/Leap_second
.. _IERS:
    https://en.wikipedia.org/wiki/
    International_Earth_Rotation_and_Reference_Systems_Service
.. _Bulletin C: https://datacenter.iers.org/productMetadata.php?id=16
