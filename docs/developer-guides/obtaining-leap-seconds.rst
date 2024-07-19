.. SPDX-FileCopyrightText: 2024 Thomas Touhey
.. SPDX-License-Identifier: GPL-3.0-only

.. _devguide-obtaining-leaps:

Obtaining a list of leap seconds
================================

.. py:currentmodule:: leapseconddata

In order to obtain the current leap second list, you must use one of
:py:class:`LeapSecondData` ``from_*`` class methods.

Using the first available standard source
-----------------------------------------

If you do not have any particular restrictions on your Internet access,
you can try the "magic" method :py:meth:`LeapSecondData.from_standard_source`,
which will try known local then network sources:

.. code-block:: python

    from leapseconddata import LeapSecondData

    data = LeapSecondData.from_standard_source()
    ...

Using a custom file source
--------------------------

If you have a custom path for the ``leap-seconds.list`` the module can use,
you can use the :py:meth:`LeapSecondData.from_file` method. For example,
if your file is located at ``/etc/my-program/leap-seconds.list``:

.. code-block:: python

    from leapseconddata import LeapSecondData

    data = LeapSecondData.from_file("/etc/my-program/leap-seconds.list")

Using a custom URL
------------------

If you have restrictions on your Internet access and can only access the
file from a specific URL available to your machine, you can use
:py:meth:`LeapSecondData.from_url`:

.. code-block:: python

    from leapseconddata import LeapSecondData

    data = LeapSecondData.from_url("https://tz.example/leap-seconds.list")

You can also still try local sources before your custom URL, by using
:py:meth:`LeapSecondData.from_standard_source` with the ``custom_sources``
keyword parameter set:

.. code-block:: python

    from leapseconddata import LeapSecondData

    data = LeapSecondData.from_standard_source(
        custom_sources=["https://tz.example/leap-seconds.list"],
    )
