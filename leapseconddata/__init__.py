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
import logging
import re
import urllib.request
from dataclasses import dataclass, field
from typing import BinaryIO, List, NamedTuple, Optional, Union

tai = datetime.timezone(datetime.timedelta(0), "TAI")

NTP_EPOCH = datetime.datetime(1900, 1, 1, tzinfo=datetime.timezone.utc)

LeapSecondInfo = NamedTuple(
    "LeapSecondInfo", (("start", datetime.datetime), ("tai", datetime.timedelta))
)

LeapSecondInfo.start.__doc__ = """The UTC timestamp just after the insertion of the leap second.

The leap second is actually the 60th second of the previous minute"""
LeapSecondInfo.tai.__doc__ = (
    """The new TAI-UTC offset.  Positive numbers indicate that TAI is ahead of UTC"""
)


class ValidityError(ValueError):
    """The leap second information is not valid for the given timestamp"""


class InvalidHashError(ValueError):
    """The file hash could not be verified"""


def _from_ntp_epoch(value: int) -> datetime.datetime:
    return NTP_EPOCH + datetime.timedelta(seconds=value)


def datetime_is_tai(when: datetime.datetime) -> bool:
    """Return true if the datetime is in the TAI timescale"""
    return when.tzname() == "TAI"


@dataclass(frozen=True)
class LeapSecondData:
    """Represent the list of known and scheduled leapseconds

    :param List[LeapSecondInfo] leap_seconds: A list of leap seconds
    :param Optional[datetime.datetime] valid_until: The expiration of the data, if available
    :param Optional[datetime.datetime] updated: The last update time of the data, if available
    """

    leap_seconds: List[LeapSecondInfo]
    """All known and scheduled leap seconds"""

    valid_until: Optional[datetime.datetime] = field(default=None)
    """The list is valid until this UTC time"""

    last_updated: Optional[datetime.datetime] = field(default=None)
    """The last time the list was updated to add a new upcoming leap second"""

    def _check_validity(self, when: Optional[datetime.datetime]) -> Optional[str]:
        if when is None:
            when = datetime.datetime.now(datetime.timezone.utc)
        if not self.valid_until:
            return "Data validity unknown"
        if when > self.valid_until:
            return f"Data only valid until {self.valid_until:%Y-%m-%d}"
        return None

    def valid(self, when: Optional[datetime.datetime] = None) -> bool:
        """Return True if the data is valid at given datetime (or the current moment, if None is passed)

        :param when: Moment to check for validity
        """
        return self._check_validity(when) is None

    @staticmethod
    def _utc_datetime(when: datetime.datetime) -> datetime.datetime:
        if when.tzinfo is not None and when.tzinfo is not datetime.timezone.utc:
            when = when.astimezone(datetime.timezone.utc)
        return when

    def tai_offset(
        self, when: datetime.datetime, check_validity: bool = True
    ) -> datetime.timedelta:
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
        for start, tai_offset in self.leap_seconds:
            if is_tai:
                start += tai_offset - datetime.timedelta(seconds=1)
            if when < start:
                return old_tai
            old_tai = tai_offset
        return self.leap_seconds[-1].tai

    def to_tai(
        self, when: datetime.datetime, check_validity: bool = True
    ) -> datetime.datetime:
        """Convert the given datetime object to TAI.

        :param when: Moment in time to convert.  If naive, it is assumed to be in UTC.
        :param check_validity: Check whether the database is valid for the given moment

        Naive timestamps are assumed to be UTC.  A TAI timestamp is returned unchanged.
        """
        if datetime_is_tai(when):
            return when
        when = self._utc_datetime(when)
        return (when + self.tai_offset(when, check_validity)).replace(tzinfo=tai)

    def tai_to_utc(
        self, when: datetime.datetime, check_validity: bool = True
    ) -> datetime.datetime:
        """Convert the given datetime object to UTC

        For a leap second, the ``fold`` property of the returned time is True.

        :param when: Moment in time to convert.  If not naive, its ``tzinfo`` must be `tai`.
        :param check_validity: Check whether the database is valid for the given moment
        """
        if when.tzinfo is not None and when.tzinfo is not tai:
            raise ValueError("Input timestamp is not TAI or naive")
        if when.tzinfo is None:
            when = when.replace(tzinfo=tai)
        result = (when - self.tai_offset(when, check_validity)).replace(
            tzinfo=datetime.timezone.utc
        )
        if self.is_leap_second(when, check_validity):
            result = result.replace(fold=True)
        return result

    def is_leap_second(
        self, when: datetime.datetime, check_validity: bool = True
    ) -> bool:
        """Return True if the given timestamp is the leap second.

        :param when: Moment in time to check.  If naive, it is assumed to be in UTC.
        :param check_validity: Check whether the database is valid for the given moment

        For a TAI timestamp, it returns True for the leap second (the one that
        would be shown as :60 in UTC).  For a UTC timestamp, it returns True
        for the :59 second if ``fold``, since the :60 second cannot be
        represented."""
        if when.tzinfo is not tai:
            when = self.to_tai(when, check_validity) + datetime.timedelta(
                seconds=when.fold
            )
        tai_offset1 = self.tai_offset(when, check_validity)
        tai_offset2 = self.tai_offset(
            when - datetime.timedelta(seconds=1), check_validity
        )
        return tai_offset1 != tai_offset2

    @classmethod
    def from_standard_source(
        cls,
        when: Optional[datetime.datetime] = None,
        check_hash: bool = True,
    ) -> LeapSecondData:
        """Get the list of leap seconds from a standard source.

        :param when: Check that the data is valid for this moment
        :param check_hash: Whether to check the embedded hash

        Using a list of standard sources, including network sources, find a
        leap-second.list data valid for the given timestamp, or the current
        time (if unspecified)"""

        for location in [  # pragma no branch
            "file:///usr/share/zoneinfo/leap-seconds.list",  # Debian Linux
            "file:///var/db/ntpd.leap-seconds.list",  # FreeBSD
            "https://raw.githubusercontent.com/eggert/tz/main/leap-seconds.list",
            "https://www.meinberg.de/download/ntp/leap-seconds.list",
        ]:
            logging.debug("Trying leap second data from %s", location)
            try:
                candidate = cls.from_url(location, check_hash)
            except InvalidHashError:  # pragma no cover
                logging.warning("Invalid hash while reading %s", location)
                continue
            if candidate is None:  # pragma no cover
                continue
            if candidate.valid(when):  # pragma no branch
                logging.info("Using leap second data from %s", location)
                return candidate
            logging.warning("Validity expired for %s", location)  # pragma no cover

        raise ValidityError(
            "No valid leap-second.list file could be found"
        )  # pragma no cover

    @classmethod
    def from_file(
        cls,
        filename: str = "/usr/share/zoneinfo/leap-seconds.list",
        check_hash: bool = True,
    ) -> LeapSecondData:
        """Retrieve the leap second list from a local file.

        :param filename: Local filename to read leap second data from.  The
            default is the standard location for the file on Debian systems.
        :param check_hash: Whether to check the embedded hash
        """
        with open(filename, "rb") as open_file:  # pragma no cover
            return cls.from_open_file(open_file, check_hash)

    @classmethod
    def from_url(
        cls,
        url: str = "https://raw.githubusercontent.com/eggert/tz/main/leap-seconds.list",
        check_hash: bool = True,
    ) -> Optional[LeapSecondData]:
        """Retrieve the leap second list from a local file

        :param filename: URL to read leap second data from.  The
            default is maintained by the tzdata authors
        :param check_hash: Whether to check the embedded hash
        """
        try:
            with urllib.request.urlopen(url) as open_file:
                return cls.from_open_file(open_file, check_hash)
        except urllib.error.URLError:  # pragma no cover
            return None

    @classmethod
    def from_data(
        cls,
        data: Union[bytes, str],
        check_hash: bool = True,
    ) -> LeapSecondData:
        """Retrieve the leap second list from local data

        :param data: Data to parse as a leap second list
        :param check_hash: Whether to check the embedded hash
        """
        if isinstance(data, str):
            data = data.encode("ascii", "replace")
        return cls.from_open_file(io.BytesIO(data), check_hash)

    @staticmethod
    def _parse_content_hash(row: bytes) -> str:
        """The SHA1 hash of the leap second content is stored in an unusual way.

        This transforms it into a string that matches `hexdigest()`"""
        parts = row.split()
        hash_parts = [int(s, 16) for s in parts[1:]]
        return "".join(f"{i:08x}" for i in hash_parts)

    @classmethod
    def from_open_file(
        cls, open_file: BinaryIO, check_hash: bool = True
    ) -> LeapSecondData:
        """Retrieve the leap second list from an open file-like object

        :param open_file: Binary IO object containing the leap second list
        :param check_hash: Whether to check the embedded hash
        """
        leap_seconds: List[LeapSecondInfo] = []
        valid_until = None
        last_updated = None
        content_to_hash = []
        content_hash = None

        hasher = hashlib.sha1()

        for row in open_file:
            row = row.strip()
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
            if len(parts) != 2:
                continue
            hasher.update(parts[0])
            hasher.update(parts[1])

            when = _from_ntp_epoch(int(parts[0]))
            tai_offset = datetime.timedelta(seconds=int(parts[1]))
            leap_seconds.append(LeapSecondInfo(when, tai_offset))

        if check_hash:
            if content_hash is None:
                raise InvalidHashError("No #h line found")
            digest = hasher.hexdigest()
            if digest != content_hash:
                raise InvalidHashError(
                    f"Hash didn't match.  Expected {content_hash[:8]}..., got {digest[:8]}..."
                )

        return LeapSecondData(leap_seconds, valid_until, last_updated)
