# SPDX-FileCopyrightText: 2022 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Commandline interface to leap second data
"""

from dataclasses import dataclass
import datetime
import logging

from . import LeapSecondData, tai

import click

utc = datetime.timezone.utc


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=utc)


class UTCDateTime(click.DateTime):
    def convert(self, value, param, ctx):
        converted = super().convert(value, param, ctx)
        if converted is not None:
            return converted.replace(tzinfo=utc)
        return converted  # pragma no cover


@dataclass
class State:
    leap_second_data: LeapSecondData


@click.group()
@click.option("--url", type=str, default=None)
@click.option("--debug/--no-debug", type=bool)
@click.pass_context
def cli(ctx, url, debug) -> None:
    if debug:  # pragma no cover
        logging.getLogger().setLevel(logging.DEBUG)
    if ctx.find_object(LeapSecondData) is None:  # pragma no branch
        if url is None:
            ctx.obj = LeapSecondData.from_standard_source()
        else:  # pragma no cover
            ctx.obj = LeapSecondData.from_url(url)


@cli.command()
@click.pass_context
def info(ctx) -> None:
    leap_second_data = ctx.obj
    print(f"Last updated: {leap_second_data.last_updated:%Y-%m-%d}")
    print(f"Valid until:  {leap_second_data.valid_until:%Y-%m-%d}")
    # The first leap_seconds entry
    print(f"{len(leap_second_data.leap_seconds)-1} leap seconds")


@cli.command()
@click.pass_context
@click.option("--tai/--utc", "is_tai", default=False)
@click.argument("timestamp", type=UTCDateTime(), default=utcnow())
def offset(ctx, is_tai, timestamp: datetime.datetime) -> None:
    leap_second_data = ctx.obj
    if is_tai:
        timestamp = timestamp.replace(tzinfo=tai)
    print(f"{leap_second_data.tai_offset(timestamp).total_seconds():.0f}")


@cli.command()
@click.pass_context
@click.option("--to-tai/--to-utc", default=True)
@click.argument("timestamp", type=UTCDateTime(), default=None, required=False)
def convert(ctx, to_tai: bool, timestamp: datetime.datetime = None) -> None:
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
@click.argument("timestamp", type=UTCDateTime(), default=utcnow())
def next_leapsecond(ctx, timestamp: datetime.datetime) -> None:
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
@click.argument("timestamp", type=UTCDateTime(), default=utcnow())
def previous_leapsecond(ctx, timestamp: datetime.datetime) -> None:
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
    "start", type=UTCDateTime(), default=datetime.datetime(1972, 1, 1, tzinfo=utc)
)
@click.argument("end", type=UTCDateTime(), default=utcnow())
@click.pass_context
def table(ctx, start, end) -> None:
    leap_second_data = ctx.obj
    for leap_second in leap_second_data.leap_seconds:  # pragma no branch
        if leap_second.start < start:
            continue
        if leap_second.start > end:
            break
        print(
            f"{leap_second.start:%Y-%m-%d}: {leap_second.tai_offset.total_seconds():.0f}"
        )


if __name__ == "__main__":  # pragma no cover
    cli()
