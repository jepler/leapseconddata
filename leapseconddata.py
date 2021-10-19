#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Use the list of known and scheduled leap seconds"""

import datetime
import hashlib
import io
import logging
import re
import urllib.request
from typing import Union, List, Optional, NamedTuple, BinaryIO

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


_LeapSecondData = NamedTuple(
    "_LeapSecondData",
    (
        ("leap_seconds", List[LeapSecondInfo]),
        ("valid_until", Optional[datetime.datetime]),
        ("last_updated", Optional[datetime.datetime]),
    ),
)

_LeapSecondData.leap_seconds.__doc__ = """All known and scheduled leap seconds"""
_LeapSecondData.valid_until.__doc__ = """The list is valid until this UTC time"""
_LeapSecondData.last_updated.__doc__ = """The last time the list was updated to add a new upcoming leap second.

It is only updated when a new leap second is scheduled, so this date may be
well in the past.  Use `valid_until` to determine validity."""


class LeapSecondData(_LeapSecondData):
    """Represent the list of known and scheduled leapseconds"""

    __slots__ = ()

    def __new__(
        cls,
        leap_seconds: List[LeapSecondInfo],
        valid_until: Optional[datetime.datetime] = None,
        last_updated: Optional[datetime.datetime] = None,
    ) -> "LeapSecondData":
        return super().__new__(cls, leap_seconds, valid_until, last_updated)

    def _check_validity(self, when: Optional[datetime.datetime]) -> Optional[str]:
        if when is None:
            when = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        if not self.valid_until:
            return "Data validity unknown"
        if when > self.valid_until:
            return f"Data only valid until {self.valid_until:%Y-%m-%d}"
        return None

    def valid(self, when: Optional[datetime.datetime] = None) -> bool:
        """Return True if the data is valid at given datetime (or the current moment, if None is passed)"""
        return self._check_validity(when) is None

    def tai_offset(
        self, when: datetime.datetime, check_validity: bool = True
    ) -> datetime.timedelta:
        """For a given datetime in UTC, return the TAI-UTC offset

        For times before the first leap second, a zero offset is returned.
        For times after the end of the file's validity, an exception is raised
        unless `check_validity=False` is passed.  In this case, it will return
        the offset of last list entry."""
        if check_validity:
            message = self._check_validity(when)
            if message is not None:
                raise ValidityError(message)

        old_tai = datetime.timedelta()
        for start, tai in self.leap_seconds:
            if when < start:
                return old_tai
            old_tai = tai
        return self.leap_seconds[-1].tai

    @classmethod
    def from_standard_source(
        cls, when: Optional[datetime.datetime] = None
    ) -> "LeapSecondData":
        """Using a list of standard sources, including network sources, find a
        leap-second.list data valid for the given timestamp, or the current
        time (if unspecified)"""

        for location in [  # pragma no branch
            "file:///usr/share/zoneinfo/leap-seconds.list",  # Linux
            "file:///var/db/ntpd.leap-seconds.list",  # FreeBSD
            "https://www.ietf.org/timezones/data/leap-seconds.list",
        ]:
            logging.debug("Trying leap second data from %s", location)
            try:
                candidate = cls.from_url(location)
            except InvalidHashError:  # pragma no cover
                logging.warning("Invalid hash while reading %s", location)
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
    ) -> "LeapSecondData":
        """Retrieve the leap second list from a local file.

        The default location is the standard location for the file on
        Debian systems."""
        with open(filename, "rb") as open_file:  # pragma no cover
            return cls.from_open_file(open_file, check_hash)

    @classmethod
    def from_url(
        cls,
        url: str = "https://www.ietf.org/timezones/data/leap-seconds.list",
        check_hash: bool = True,
    ) -> "LeapSecondData":
        """Retrieve the leap second list from a local file

        The default location is the official copy of the data from IETF"""
        with urllib.request.urlopen(url) as open_file:
            return cls.from_open_file(open_file, check_hash)

    @classmethod
    def from_data(
        cls,
        data: Union[bytes, str],
        check_hash: bool = True,
    ) -> "LeapSecondData":
        """Retrieve the leap second list from local data"""
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
    ) -> "LeapSecondData":
        """Retrieve the leap second list from an open file-like object"""
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
            content_to_hash.extend(re.findall(br"\d+", row))

            parts = row.split()
            if len(parts) != 2:
                continue
            hasher.update(parts[0])
            hasher.update(parts[1])

            when = _from_ntp_epoch(int(parts[0]))
            tai = datetime.timedelta(seconds=int(parts[1]))
            leap_seconds.append(LeapSecondInfo(when, tai))

        if check_hash:
            if content_hash is None:
                raise InvalidHashError("No #h line found")
            digest = hasher.hexdigest()
            if digest != content_hash:
                raise InvalidHashError(
                    f"Hash didn't match.  Expected {content_hash[:8]}..., got {digest[:8]}..."
                )

        return LeapSecondData(leap_seconds, valid_until, last_updated)


def main() -> None:
    """When run as a main program, print some information about leap seconds"""
    logging.getLogger().setLevel(logging.INFO)
    lsd = LeapSecondData.from_standard_source()
    print(f"Last updated: {lsd.last_updated:%Y-%m-%d}")
    print(f"Valid until:  {lsd.valid_until:%Y-%m-%d}")
    for when, offset in lsd.leap_seconds[-10:]:
        print(f"{when:%Y-%m-%d}: {offset.total_seconds()}")
    when = datetime.datetime(2011, 1, 1, tzinfo=datetime.timezone.utc)
    print(f"TAI-UTC on {when:%Y-%m-%d} was {lsd.tai_offset(when).total_seconds()}")


if __name__ == "__main__":  # pragma no cover
    main()
