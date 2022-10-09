# SPDX-FileCopyrightText: 2022 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Smoke test program for leapseconddata

If this was a useful program, it would be exposed as an entry point in setup.cfg.
"""

import datetime
import logging

from . import LeapSecondData


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

    when_tai = lsd.to_tai(when)
    when_rt = lsd.tai_to_utc(when_tai)
    print(f"{when:%Y-%m-%d %H:%M:%S} UTC -> {when_tai:%Y-%m-%d %H:%M:%S} TAI")
    print(f"{when_tai:%Y-%m-%d %H:%M:%S} TAI -> {when_rt:%Y-%m-%d %H:%M:%S} UTC")
    print(f"is leap second? {lsd.is_leap_second(when)}")

    u = datetime.datetime(
        1999, 1, 1, tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(seconds=2)
    t = lsd.to_tai(u)

    print("replaying leapsecond at end of 1998")
    for _ in range(5):
        print(
            f"{u:%Y-%m-%d %H:%M:%S} UTC {'LS' if u.fold else '  '} = {t:%Y-%m-%d %H:%M:%S} TAI {'LS' if lsd.is_leap_second(t) else '  '}"
        )
        t += datetime.timedelta(seconds=1)
        u = lsd.tai_to_utc(t)


if __name__ == "__main__":  # pragma no cover
    main()
