#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Test most leapseconddata functionality"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import datetime
import unittest
import leapseconddata

db = leapseconddata.LeapSecondData.from_standard_source()


class LeapSecondDataTest(unittest.TestCase):
    def test_main(self) -> None:  # pylint: disable=no-self-use
        leapseconddata.main()

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
