# SPDX-FileCopyrightText: 2022 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""Commandline interface to leap second data"""

from __future__ import annotations

import datetime
import logging
import typing
from dataclasses import dataclass

import click

from . import LeapSecondData, tai

utc = datetime.timezone.utc


def utcnow() -> datetime.datetime:
    """Return the current time in UTC, with tzinfo=utc"""
    return datetime.datetime.now(utc)


class UTCDateTime(click.DateTime):
    """Click option class for date time in UTC"""

    def convert(
        self,
        value: typing.Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> typing.Any:
        """Convert the value then attach the utc timezone"""
        converted = super().convert(value, param, ctx)
        if converted is not None:
            return converted.replace(tzinfo=utc)
        return converted  # pragma no cover


@dataclass
class State:
    """State shared across sub-commands"""

    leap_second_data: LeapSecondData


@click.group()
@click.option(
    "--url",
    type=str,
    default=None,
    help="URL for leap second data (unspecified to use default source",
)
@click.option("--debug/--no-debug", type=bool)
@click.pass_context
def cli(ctx: click.Context, *, url: str, debug: bool) -> None:
    """Access leap second database information"""
    if debug:  # pragma no cover
        logging.getLogger().setLevel(logging.DEBUG)
    if ctx.find_object(LeapSecondData) is None:  # pragma no branch
        if url is None:
            ctx.obj = LeapSecondData.from_standard_source()
        else:  # pragma no cover
            ctx.obj = LeapSecondData.from_url(url)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information about leap second database"""
    leap_second_data = ctx.obj
    print(f"Last updated: {leap_second_data.last_updated:%Y-%m-%d}")
    print(f"Valid until:  {leap_second_data.valid_until:%Y-%m-%d}")
    # The first leap_seconds entry
    print(f"{len(leap_second_data.leap_seconds)-1} leap seconds")


@cli.command()
@click.pass_context
@click.option("--tai/--utc", "is_tai", default=False)
@click.argument("timestamp", type=UTCDateTime(), default=utcnow(), metavar="TIMESTAMP")
def offset(ctx: click.Context, *, is_tai: bool, timestamp: datetime.datetime) -> None:
    """Get the UTC offset for a given moment, in seconds"""
    leap_second_data = ctx.obj
    if is_tai:
        timestamp = timestamp.replace(tzinfo=tai)
    print(f"{leap_second_data.tai_offset(timestamp).total_seconds():.0f}")


@cli.command()
@click.pass_context
@click.option("--to-tai/--to-utc", default=True)
@click.argument("timestamp", type=UTCDateTime(), default=None, required=False, metavar="TIMESTAMP")
def convert(ctx: click.Context, *, to_tai: bool, timestamp: datetime.datetime | None = None) -> None:
    """Convert timestamps between TAI and UTC"""
    leap_second_data = ctx.obj
    if to_tai:
        if timestamp is None:
            timestamp = utcnow()
        when_tai = leap_second_data.to_tai(timestamp)
        print(f"{when_tai:%Y-%m-%d %H:%M:%S} TAI")
    else:
        if timestamp is None:  # pragma no cover
            raise click.UsageError("--to-utc requires explicit timestamp", ctx)
        when_utc = leap_second_data.tai_to_utc(timestamp.replace(tzinfo=tai))
        if when_utc.fold:
            print(f"{when_utc:%Y-%m-%d %H:%M:60} UTC")
        else:
            print(f"{when_utc:%Y-%m-%d %H:%M:%S} UTC")


@cli.command()
@click.pass_context
@click.argument("timestamp", type=UTCDateTime(), default=utcnow(), metavar="TIMESTAMP")
def next_leapsecond(ctx: click.Context, *, timestamp: datetime.datetime) -> None:
    """Get the next leap second after a given UTC timestamp"""
    leap_second_data = ctx.obj
    ls = min(
        (ls for ls in leap_second_data.leap_seconds if ls.start > timestamp),
        default=None,
        key=lambda x: x.start,
    )
    if ls is None:
        print("None")
    else:
        print(f"{ls.start:%Y-%m-%d %H:%M:%S} UTC")


@cli.command()
@click.pass_context
@click.argument("timestamp", type=UTCDateTime(), default=utcnow(), metavar="TIMESTAMP")
def previous_leapsecond(ctx: click.Context, *, timestamp: datetime.datetime) -> None:
    """Get the last leap second before a given UTC timestamp"""
    leap_second_data = ctx.obj
    ls = max(
        (ls for ls in leap_second_data.leap_seconds if ls.start < timestamp),
        default=None,
        key=lambda x: x.start,
    )
    if ls is None:
        print("None")
    else:
        print(f"{ls.start:%Y-%m-%d %H:%M:%S} UTC")


@cli.command()
@click.argument(
    "start",
    type=UTCDateTime(),
    default=datetime.datetime(1972, 1, 1, tzinfo=utc),
    metavar="START-TIMESTAMP",
)
@click.argument("end", type=UTCDateTime(), default=utcnow(), metavar="[END-TIMESTAMP]")
@click.pass_context
def table(ctx: click.Context, *, start: datetime.datetime, end: datetime.datetime) -> None:
    """Print information about leap seconds"""
    leap_second_data = ctx.obj
    for leap_second in leap_second_data.leap_seconds:  # pragma no branch
        if leap_second.start < start:
            continue
        if leap_second.start > end:
            break
        print(f"{leap_second.start:%Y-%m-%d}: {leap_second.tai_offset.total_seconds():.0f}")


if __name__ == "__main__":  # pragma no cover
    cli()
