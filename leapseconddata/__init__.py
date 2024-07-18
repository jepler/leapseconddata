#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Use the list of known and scheduled leap seconds

For example, to retrieve the UTC-TAI offset on January 1, 2011:

.. code-block:: python
    :emphasize-lines: 2,3,5

    >>> import datetime
    >>> import leapseconddata
    >>> ls = leapseconddata.LeapSecondData.from_standard_source()
    >>> when = datetime.datetime(2011, 1, 1, tzinfo=datetime.timezone.utc)
    >>> ls.tai_offset(when).total_seconds()
    34.0

"""

from __future__ import annotations

import datetime
import hashlib
import io
import itertools
import logging
import pathlib
import re
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, BinaryIO, ClassVar

if TYPE_CHECKING:  # pragma no cover
    from collections.abc import Sequence

tai = datetime.timezone(datetime.timedelta(0), "TAI")

NTP_EPOCH = datetime.datetime(1900, 1, 1, tzinfo=datetime.timezone.utc)


@dataclass(frozen=True)
class LeapSecondInfo:
    """Information about a particular leap second"""

    start: datetime.datetime
    """The UTC timestamp just after the insertion of the leap second.

    The leap second is actually the 61th second of the previous minute (xx:xx:60)"""

    tai_offset: datetime.timedelta
    """The new TAI-UTC offset.  Positive numbers indicate that TAI is ahead of UTC"""


class ValidityError(ValueError):
    """The leap second information is not valid for the given timestamp"""


class InvalidHashError(ValueError):
    """The file hash could not be verified"""


class InvalidContentError(ValueError):
    """A line in the file was not valid"""


def _from_ntp_epoch(value: int) -> datetime.datetime:
    return NTP_EPOCH + datetime.timedelta(seconds=value)


def datetime_is_tai(when: datetime.datetime) -> bool:
    """Return true if the datetime is in the TAI timescale"""
    return when.tzname() == "TAI"


@dataclass(frozen=True)
class LeapSecondData:
    """Represent the list of known and scheduled leapseconds

    :param List[LeapSecondInfo] leap_seconds: A list of leap seconds
    :param Optional[datetime.datetime] valid_until: The expiration of the data
    :param Optional[datetime.datetime] updated: The last update time of the data
    """

    standard_file_sources: ClassVar[list[str]] = [
        "file:///usr/share/zoneinfo/leap-seconds.list",  # Debian Linux
        "file:///var/db/ntpd.leap-seconds.list",  # FreeBSD
    ]
    """When using `LeapSecondData.from_standard_source`, these local sources are checked first.

    Locations for Debian Linux & FreeBSD are supported."""

    standard_network_sources: ClassVar[list[str]] = [
        "https://hpiers.obspm.fr/iers/bul/bulc/ntp/leap-seconds.list",
        "https://data.iana.org/time-zones/tzdb/leap-seconds.list",
        "https://raw.githubusercontent.com/eggert/tz/main/leap-seconds.list",
        "ftp://ftp.boulder.nist.gov/pub/time/leap-seconds.list",
        "https://www.meinberg.de/download/ntp/leap-seconds.list",
    ]
    """When using `LeapSecondData.from_standard_source`, these network sources are checked second.

    Remote sources are checked in the following order until a suitable file is found:

     * The `International Earth Rotation Service (IERS)
       <https://www.iers.org/IERS/EN/Home/home_node.html>`_ is the international
       body charged with various duties including scheduling leap seconds.
     * The `Internet Assigned Numbers Authority (IANA)
       <https://www.iana.org/>`_ publishes the IANA timezone database, used by
       many major operating sytsems for handling the world's time zones. As part
       of this activity they publish a version of the leap second list.
     * `eggert/tz <https://github.com/eggert/tz>`_ is the canonical github home
       of the IANA timezone database, and updated versions of the leap second
       list can appear here before they are part of an official IANA timezone
       database release.
     * `The National Institute of Standards and Technology (NIST)'s Time
       Realization and Distribution Group
       <https://www.nist.gov/pml/time-and-frequency-division/time-distribution/internet-time-service-its>`_
       is a US federal organization that publishes a version of the leap second
       database.
     * `Meinberg Funkuhren GmbH & Co. KG
       <https://www.meinbergglobal.com/english/company/>`_ is a Germany-based
       company that published a `helpful article in its knowledge base
       <https://kb.meinbergglobal.com/kb/time_sync/ntp/configuration/ntp_leap_second_file>`_
       including URLs of sites that disseminate the leap second list. They state
       that the version they distribute is frequently more up to date than other
       sources, including IANA, NIST, and tzdb."""

    leap_seconds: list[LeapSecondInfo]
    """All known and scheduled leap seconds"""

    valid_until: datetime.datetime | None = field(default=None)
    """The list is valid until this UTC time"""

    last_updated: datetime.datetime | None = field(default=None)
    """The last time the list was updated to add a new upcoming leap second"""

    def _check_validity(self, when: datetime.datetime | None) -> str | None:
        if when is None:
            when = datetime.datetime.now(datetime.timezone.utc)
        if not self.valid_until:
            return "Data validity unknown"
        if when > self.valid_until:
            return f"Data only valid until {self.valid_until:%Y-%m-%d}"
        return None

    def valid(self, when: datetime.datetime | None = None) -> bool:
        """Return True if the data is valid at given datetime

        If `when` is none, the validity for the current moment is checked.

        :param when: Moment to check for validity
        """
        return self._check_validity(when) is None

    @staticmethod
    def _utc_datetime(when: datetime.datetime) -> datetime.datetime:
        if when.tzinfo is not None and when.tzinfo is not datetime.timezone.utc:
            when = when.astimezone(datetime.timezone.utc)
        return when

    def tai_offset(self, when: datetime.datetime, *, check_validity: bool = True) -> datetime.timedelta:
        """For a given datetime, return the TAI-UTC offset

        :param when: Moment in time to find offset for
        :param check_validity: Check whether the database is valid for the given moment

        For times before the first leap second, a zero offset is returned.
        For times after the end of the file's validity, an exception is raised
        unless `check_validity=False` is passed.  In this case, it will return
        the offset of the last list entry.
        """
        is_tai = datetime_is_tai(when)
        if not is_tai:
            when = self._utc_datetime(when)
        if check_validity:
            message = self._check_validity(when)
            if message is not None:
                raise ValidityError(message)

        if not self.leap_seconds:
            return datetime.timedelta(0)

        old_tai = datetime.timedelta()
        for leap_second in self.leap_seconds:
            start = leap_second.start
            if is_tai:
                start += leap_second.tai_offset - datetime.timedelta(seconds=1)
            if when < start:
                return old_tai
            old_tai = leap_second.tai_offset
        return self.leap_seconds[-1].tai_offset

    def to_tai(self, when: datetime.datetime, *, check_validity: bool = True) -> datetime.datetime:
        """Convert the given datetime object to TAI.

        :param when: Moment in time to convert.  If naive, it is assumed to be in UTC.
        :param check_validity: Check whether the database is valid for the given moment

        Naive timestamps are assumed to be UTC.  A TAI timestamp is returned unchanged.
        """
        if datetime_is_tai(when):
            return when
        when = self._utc_datetime(when)
        return (when + self.tai_offset(when, check_validity=check_validity)).replace(tzinfo=tai)

    def tai_to_utc(self, when: datetime.datetime, *, check_validity: bool = True) -> datetime.datetime:
        """Convert the given datetime object to UTC

        For a leap second, the ``fold`` property of the returned time is True.

        :param when: Moment in time to convert.  If not naive, its ``tzinfo`` must be `tai`.
        :param check_validity: Check whether the database is valid for the given moment
        """
        if when.tzinfo is not None and when.tzinfo is not tai:
            raise ValueError("Input timestamp is not TAI or naive")
        if when.tzinfo is None:
            when = when.replace(tzinfo=tai)
        result = (when - self.tai_offset(when, check_validity=check_validity)).replace(tzinfo=datetime.timezone.utc)
        if self.is_leap_second(when, check_validity=check_validity):
            result = result.replace(fold=True)
        return result

    def is_leap_second(self, when: datetime.datetime, *, check_validity: bool = True) -> bool:
        """Return True if the given timestamp is the leap second.

        :param when: Moment in time to check.  If naive, it is assumed to be in UTC.
        :param check_validity: Check whether the database is valid for the given moment

        For a TAI timestamp, it returns True for the leap second (the one that
        would be shown as :60 in UTC).  For a UTC timestamp, it returns True
        for the :59 second if ``fold``, since the :60 second cannot be
        represented.
        """
        if when.tzinfo is not tai:
            when = self.to_tai(when, check_validity=check_validity) + datetime.timedelta(seconds=when.fold)
        tai_offset1 = self.tai_offset(when, check_validity=check_validity)
        tai_offset2 = self.tai_offset(when - datetime.timedelta(seconds=1), check_validity=check_validity)
        return tai_offset1 != tai_offset2

    @classmethod
    def from_standard_source(
        cls,
        when: datetime.datetime | None = None,
        *,
        check_hash: bool = True,
        custom_sources: Sequence[str] = (),
    ) -> LeapSecondData:
        """Get the list of leap seconds from a standard source.

        :param when: Check that the data is valid for this moment
        :param check_hash: Whether to check the embedded hash

        Using a list of standard sources, including network sources, find a
        leap-second.list data valid for the given timestamp, or the current
        time (if unspecified)

        If ``custom_sources`` is specified, this list of URLs is checked before
        the hard-coded sources.
        """
        for location in itertools.chain(custom_sources, cls.standard_file_sources, cls.standard_network_sources):
            logging.debug("Trying leap second data from %s", location)
            try:
                candidate = cls.from_url(location, check_hash=check_hash)
            except InvalidHashError:
                logging.warning("Invalid hash while reading %s", location)
                continue
            except InvalidContentError as e:
                logging.warning("Invalid content while reading %s: %s", location, e)
                continue
            if candidate is None:
                continue
            if candidate.valid(when):
                logging.info("Using leap second data from %s", location)
                return candidate
            logging.warning("Validity expired for %s", location)

        raise ValidityError("No valid leap-second.list file could be found")

    @classmethod
    def from_file(
        cls,
        filename: str = "/usr/share/zoneinfo/leap-seconds.list",
        *,
        check_hash: bool = True,
    ) -> LeapSecondData:
        """Retrieve the leap second list from a local file.

        :param filename: Local filename to read leap second data from.  The
            default is the standard location for the file on Debian systems.
        :param check_hash: Whether to check the embedded hash
        """
        with pathlib.Path(filename).open("rb") as open_file:  # pragma no cover
            return cls.from_open_file(open_file, check_hash=check_hash)

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        check_hash: bool = True,
    ) -> LeapSecondData | None:
        """Retrieve the leap second list from a local file

        :param filename: URL to read leap second data from
        :param check_hash: Whether to check the embedded hash
        """
        try:
            with urllib.request.urlopen(url) as open_file:
                return cls.from_open_file(open_file, check_hash=check_hash)
        except urllib.error.URLError:  # pragma no cover
            return None

    @classmethod
    def from_data(
        cls,
        data: bytes | str,
        *,
        check_hash: bool = True,
    ) -> LeapSecondData:
        """Retrieve the leap second list from local data

        :param data: Data to parse as a leap second list
        :param check_hash: Whether to check the embedded hash
        """
        if isinstance(data, str):
            data = data.encode("ascii", "replace")
        return cls.from_open_file(io.BytesIO(data), check_hash=check_hash)

    @staticmethod
    def _parse_content_hash(row: bytes) -> str:
        """Transform the SHA1 content into a string that matches `hexdigest()`

        The SHA1 hash of the leap second content is stored in an unusual way.
        """
        parts = row.split()
        hash_parts = [int(s, 16) for s in parts[1:]]
        return "".join(f"{i:08x}" for i in hash_parts)

    @classmethod
    def from_open_file(cls, open_file: BinaryIO, *, check_hash: bool = True) -> LeapSecondData:
        """Retrieve the leap second list from an open file-like object

        :param open_file: Binary IO object containing the leap second list
        :param check_hash: Whether to check the embedded hash
        """
        leap_seconds: list[LeapSecondInfo] = []
        valid_until = None
        last_updated = None
        content_to_hash = []
        content_hash = None

        hasher = hashlib.sha1()

        for row_ws in open_file:
            row = row_ws.strip()
            try:
                if row.startswith(b"#h"):
                    content_hash = cls._parse_content_hash(row)
                    continue

                if row.startswith(b"#@"):
                    parts = row.split()
                    hasher.update(parts[1])
                    valid_until = _from_ntp_epoch(int(parts[1]))
                    continue

                if row.startswith(b"#$"):
                    parts = row.split()
                    hasher.update(parts[1])
                    last_updated = _from_ntp_epoch(int(parts[1]))
                    continue

                row = row.split(b"#")[0].strip()
                content_to_hash.extend(re.findall(rb"\d+", row))

                parts = row.split()
                if len(parts) != 2:  # noqa: PLR2004
                    continue
                hasher.update(parts[0])
                hasher.update(parts[1])

                when = _from_ntp_epoch(int(parts[0]))
                tai_offset = datetime.timedelta(seconds=int(parts[1]))
                leap_seconds.append(LeapSecondInfo(when, tai_offset))
            except Exception as e:
                raise InvalidContentError(f"Failed to parse: {row!r}: {e}") from e

        if check_hash:
            if content_hash is None:
                raise InvalidHashError("No #h line found")
            digest = hasher.hexdigest()
            if digest != content_hash:
                raise InvalidHashError(f"Hash didn't match.  Expected {content_hash[:8]}..., got {digest[:8]}...")

        return LeapSecondData(leap_seconds, valid_until, last_updated)
