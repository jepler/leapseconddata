#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Test most leapseconddata functionality"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import datetime
import unittest

import leapseconddata
import leapseconddata.__main__

db = leapseconddata.LeapSecondData.from_standard_source()

GMT1 = datetime.timezone(datetime.timedelta(seconds=3600), "GMT1")


class LeapSecondDataTest(unittest.TestCase):
    def test_main(self) -> None:
        leapseconddata.__main__.main()

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
        self.assertIsNotNone(
            leapseconddata.LeapSecondData.from_data("#h 0 0 0 0 0\n", False)
        )

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
                )
            ]
        )
        self.assertRaises(leapseconddata.ValidityError, db1.tai_offset, db.valid_until)
        self.assertEqual(
            db1.tai_offset(valid_until, False), datetime.timedelta(seconds=1)
        )

        when = datetime.datetime(
            1999, 1, 1, tzinfo=datetime.timezone.utc
        ) - datetime.timedelta(seconds=1)
        assert when.tzinfo is not None
        self.assertRaises(ValueError, db.tai_to_utc, when)

    def test_empty(self) -> None:
        db1 = leapseconddata.LeapSecondData([])
        self.assertEqual(
            db1.tai_offset(datetime.datetime(2020, 1, 1), False),
            datetime.timedelta(seconds=0),
        )

    def test_tz(self) -> None:
        when = datetime.datetime(
            1999, 1, 1, tzinfo=datetime.timezone.utc
        ) - datetime.timedelta(seconds=1)
        when = when.replace(fold=True)
        self.assertTrue(db.is_leap_second(when))
        self.assertFalse(db.is_leap_second(when - datetime.timedelta(seconds=1)))
        self.assertFalse(db.is_leap_second(when + datetime.timedelta(seconds=1)))

        when = when.astimezone(GMT1).replace(fold=True)
        self.assertTrue(db.is_leap_second(when))
        self.assertFalse(db.is_leap_second(when - datetime.timedelta(seconds=1)))
        self.assertFalse(db.is_leap_second(when + datetime.timedelta(seconds=1)))

        when_tai = datetime.datetime(1999, 1, 1, 0, 0, 32)
        when_utc = db.tai_to_utc(when_tai)
        self.assertIs(when_utc.tzinfo, datetime.timezone.utc)
        print(when_utc)

    def test_to_tai(self) -> None:
        when = datetime.datetime(
            1999, 1, 1, tzinfo=datetime.timezone.utc
        ) - datetime.timedelta(seconds=1)
        when_tai = db.to_tai(when)
        when_tai2 = db.to_tai(when_tai)
        assert when != when_tai
        assert when_tai == when_tai2
        assert when_tai.tzinfo is leapseconddata.tai
        assert when_tai2.tzinfo is leapseconddata.tai


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
