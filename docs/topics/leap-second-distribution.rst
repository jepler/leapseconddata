.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

How is leap second data distributed?
====================================

Leap seconds are announced **every six months** by the IERS in the
`Bulletin C publications`_:

* On beginning of January if they are introduced on June 30th (UTC);
* On beginning of July if they are introduced in December 31st (UTC).

For example:

* `Bulletin C 52`_, published on July 6th, 2016, announces a leap
  second will be introduced on December 31st, 2016 (UTC).
* `Bulletin C 67`_, published on July 4th, 2024, announces **no**
  leap second will be introduced on June 30th, 2024 (UTC).

The IERS also distributes a file named ``leap-seconds.list``, at the
following URL::

    https://hpiers.obspm.fr/iers/bul/bulc/ntp/leap-seconds.list

From here, there are multiple approaches to how systems can receive
the information, in order to display the time correctly:

* NTP supports informing clients of minutes with a leap second.
  See `The NTP Timescale and Leap Seconds`_ for more information;
* Debian and derivatives distribute the file provided by the IERS, as
  well as some commodities, through the tzdata_ package.
  This file is available at ``/usr/share/zoneinfo/leap-seconds.list``;
* FreeBSD's ntpd has a ntpleapfetch_ command that fetches ``leap-seconds.list``
  file, and stores it in ``/var/db/ntpd.leap-seconds.list``.
* Programs can fetch the file directly from network sources, if the network
  is not restricted.

If using :py:meth:`LeapSecondData.from_standard_source`, ``leapseconddata``
will use local sources if available, and official network sources if
not found.

.. _Bulletin C publications:
    https://datacenter.iers.org/availableVersions.php?id=16
.. _Bulletin C 52:
    https://datacenter.iers.org/data/16/bulletinc-052.txt
.. _Bulletin C 67:
    https://datacenter.iers.org/data/16/bulletinc-067.txt
.. _The NTP Timescale and Leap Seconds: https://www.ntp.org/reflib/leap/
.. _tzdata: https://salsa.debian.org/glibc-team/tzdata
.. _ntpleapfetch: https://docs.ntpsec.org/latest/ntpleapfetch.html
