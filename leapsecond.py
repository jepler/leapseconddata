#!/usr/bin/env python3
import collections
import datetime
import hashlib
import re
import urllib.request
from typing import List, Tuple, Optional, NamedTuple, BinaryIO

NTP_EPOCH = datetime.datetime(1900,1,1, tzinfo=datetime.timezone.utc)

LeapSecondInfo = NamedTuple("LeapSecondInfo", (("start", datetime.datetime), ("tai", datetime.timedelta)))

def _from_ntp_epoch(value: int) -> datetime.datetime:
    return NTP_EPOCH + datetime.timedelta(seconds=value)

_LeapSecondDatabase = NamedTuple("_LeapSecondDatabase", (
    ("leap_seconds", List[LeapSecondInfo]),
    ("valid_until", Optional[datetime.datetime]),
    ("last_updated", Optional[datetime.datetime])))

class LeapSecondDatabase(_LeapSecondDatabase):
    def __new__(cls, leap_seconds: List[LeapSecondInfo], valid_until:Optional[datetime.datetime]=None, last_updated:Optional[datetime.datetime]=None) -> "LeapSecondDatabase":
        return super().__new__(cls, leap_seconds, valid_until, last_updated)

    def tai_offset(self, dt: datetime.datetime, check_validity:bool=True) -> Optional[datetime.timedelta]:
        """For a given datetime in UTC, return the TAI-UTC offset"""
        if check_validity:
            if not self.valid_until:
                raise ValueError("Database validity unknown")
            if dt > self.valid_until:
                raise ValueError("Database only valid until {self.valid_until:%Y-%m-%d}")

        old_tai = datetime.timedelta()
        for start, tai in self.leap_seconds:
            if dt < start:
                return old_tai
            old_tai = tai
        return self.leap_seconds[-1].tai

    @classmethod
    def from_file(cls, filename: str="/usr/share/zoneinfo/leap-seconds.list", check_hash:bool=True) -> "LeapSecondDatabase":
        with open(filename, "rb") as f:
            return cls.from_open_file(f, check_hash)

    @classmethod
    def from_url(cls, url:str="https://www.ietf.org/timezones/data/leap-seconds.list", check_hash:bool=True) -> "LeapSecondDatabase":
        with urllib.request.urlopen(url) as f:
            return cls.from_open_file(f, check_hash)

    @staticmethod
    def _parse_content_hash(row: bytes) -> str:
        parts = row.split()
        hash_parts = [int(s, 16) for s in parts[1:]]
        return "".join("%08x" % i for i in hash_parts)

    @classmethod
    def from_open_file(cls, f: BinaryIO, check_hash:bool=True) -> "LeapSecondDatabase":
        leap_seconds: List[LeapSecondInfo] = []
        valid_until = None
        last_updated = None
        content_to_hash = []
        content_hash = None

        s = hashlib.sha1()

        for row in f:
            row = row.strip()
            if row.startswith(b"#h"):
                content_hash = cls._parse_content_hash(row)
                continue

            if row.startswith(b"#@"):
                parts = row.split()
                s.update(parts[1])
                valid_until = _from_ntp_epoch(int(parts[1]))
                continue

            if row.startswith(b"#$"):
                parts = row.split()
                s.update(parts[1])
                last_updated = _from_ntp_epoch(int(parts[1]))
                continue

            row = row.split(b"#")[0].strip()
            content_to_hash.extend(re.findall(br"\d+", row))

            parts = row.split()
            if len(parts) != 2:
                continue
            s.update(parts[0])
            s.update(parts[1])

            when = _from_ntp_epoch(int(parts[0]))
            tai = datetime.timedelta(seconds=int(parts[1]))
            leap_seconds.append(LeapSecondInfo(when, tai))

        if check_hash:
            if content_hash is None:
                raise ValueError("No #h line found")
            digest = s.hexdigest()
            print(f"NOTE: {digest=}")
            if digest != content_hash:
                raise ValueError(f"Hash didn't match.  Expected {content_hash[:8]}..., got {digest[:8]}...")

        return LeapSecondDatabase(leap_seconds, valid_until, last_updated)

if __name__ == '__main__':
    lsd = LeapSecondDatabase.from_url()
    print(f"Last updated: {lsd.last_updated:%Y-%m-%d}")
    print(f"Valid until:  {lsd.valid_until:%Y-%m-%d}")
    for a, b in lsd.leap_seconds[-10:]:
        print(f"{a:%Y-%m-%d}: {b.total_seconds()}")
    print(f"TAI-UTC on 2011-01-01: {lsd.tai_offset(datetime.datetime(2011, 1, 1, tzinfo=datetime.timezone.utc))}")
