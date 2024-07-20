#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

# ruff: noqa: D101
# ruff: noqa: D102

"""Test most leapseconddata functionality"""

import contextlib
import datetime
import io
import pathlib
import unittest

import leapseconddata
import leapseconddata.__main__

db = leapseconddata.LeapSecondData.from_standard_source()

GMT1 = datetime.timezone(datetime.timedelta(seconds=3600), "GMT1")


class LeapSecondDataTest(unittest.TestCase):
    def run_main(self, *args: str) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                leapseconddata.__main__.cli(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

    def test_main(self) -> None:
        self.run_main("info")
        self.run_main("table", "2009-1-1", "2016-1-1")
        self.run_main("convert", "--to-utc", "2009-01-01 00:00:33")
        self.run_main("convert", "--to-utc", "2009-01-01 00:00:34")
        self.run_main("convert", "2009-01-01 00:00:33")
        self.run_main("convert")
        self.run_main("offset", "2009-01-01 00:00:33")
        self.run_main("offset", "--tai", "2009-01-01 00:00:33")
        self.run_main("next-leapsecond", "2009-2-2")
        self.run_main("next-leapsecond", "2100-2-2")
        self.run_main("previous-leapsecond", "2009-2-2")
        self.run_main("previous-leapsecond", "1960-2-2")
        self.run_main("sources")

    def test_corrupt(self) -> None:
        self.assertRaises(
            leapseconddata.InvalidHashError,
            leapseconddata.LeapSecondData.from_data,
            "#h 0 0 0 0 0\n",
        )
        self.assertRaises(
            leapseconddata.InvalidHashError,
            leapseconddata.LeapSecondData.from_data,
            b"#h 0 0 0 0 0\n",
        )
        self.assertRaises(
            leapseconddata.InvalidHashError,
            leapseconddata.LeapSecondData.from_data,
            "#\n",
        )
        self.assertIsNotNone(leapseconddata.LeapSecondData.from_data("#h 0 0 0 0 0\n", check_hash=False))

    def test_invalid(self) -> None:
        valid_until = db.valid_until
        assert valid_until
        self.assertRaises(
            leapseconddata.ValidityError,
            db.tai_offset,
            valid_until + datetime.timedelta(seconds=1),
        )
        db1 = leapseconddata.LeapSecondData(
            [
                leapseconddata.LeapSecondInfo(
                    datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc),
                    datetime.timedelta(seconds=1),
                ),
            ],
        )
        self.assertRaises(leapseconddata.ValidityError, db1.tai_offset, db.valid_until)
        self.assertEqual(db1.tai_offset(valid_until, check_validity=False), datetime.timedelta(seconds=1))

        when = datetime.datetime(1999, 1, 1, tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=1)
        assert when.tzinfo is not None
        self.assertRaises(ValueError, db.tai_to_utc, when)

    def test_empty(self) -> None:
        db1 = leapseconddata.LeapSecondData([])
        self.assertEqual(
            db1.tai_offset(datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc), check_validity=False),
            datetime.timedelta(seconds=0),
        )

    def test_invalid2(self) -> None:
        when = datetime.datetime(datetime.MAXYEAR, 1, 1, tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=1)
        with self.assertRaises(leapseconddata.ValidityError):
            leapseconddata.LeapSecondData.from_standard_source(
                when,
                custom_sources=[
                    "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==",
                    "data:text/plain,%23h%099dac5845%208acd32c0%202947d462%20daf4a943%20f58d9391%0A",
                    "file:///doesnotexist",
                ],
            )

    def test_tz(self) -> None:
        when = datetime.datetime(1999, 1, 1, tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=1)
        when = when.replace(fold=True)
        self.assertTrue(db.is_leap_second(when))
        self.assertFalse(db.is_leap_second(when - datetime.timedelta(seconds=1)))
        self.assertFalse(db.is_leap_second(when + datetime.timedelta(seconds=1)))

        when = when.astimezone(GMT1).replace(fold=True)
        self.assertTrue(db.is_leap_second(when))
        self.assertFalse(db.is_leap_second(when - datetime.timedelta(seconds=1)))
        self.assertFalse(db.is_leap_second(when + datetime.timedelta(seconds=1)))

        when_tai = datetime.datetime(1999, 1, 1, 0, 0, 32, tzinfo=leapseconddata.tai)
        when_utc = db.tai_to_utc(when_tai)
        self.assertIs(when_utc.tzinfo, datetime.timezone.utc)

        when_tai = datetime.datetime(1999, 1, 1, 0, 0, 32, tzinfo=None)  # noqa: DTZ001
        when_utc2 = db.tai_to_utc(when_tai)
        self.assertEqual(when_utc, when_utc2)

    def test_to_tai(self) -> None:
        when = datetime.datetime(1999, 1, 1, tzinfo=datetime.timezone.utc) - datetime.timedelta(seconds=1)
        when_tai = db.to_tai(when)
        when_tai2 = db.to_tai(when_tai)
        assert when != when_tai
        assert when_tai == when_tai2
        assert when_tai.tzinfo is leapseconddata.tai
        assert when_tai2.tzinfo is leapseconddata.tai

    def assertPrints(self, code: str, expected: str) -> None:  # noqa: N802
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(code, {}, {})
        self.assertEqual(expected, buf.getvalue())

    def test_doc(self) -> None:
        docs = pathlib.Path(__file__).parent / "docs"
        for expected in docs.rglob("**/*.py.exp"):
            py = expected.with_suffix("")  # Pop off the ".exp" suffix
            self.assertPrints(py.read_text(encoding="utf-8"), expected.read_text(encoding="utf-8"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
