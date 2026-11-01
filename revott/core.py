"""The coordinate system.

Everything here is exact.  TNLDY is the coordinate; a calendar date and a
decimal year are two readings of it, and neither is primary.

    TNLDY(Y, X) = 14160 + 100·Y + 100·X
    year(TNLDY) = TNLDY × 23/8400 + 1969 + 391/420
    date(TNLDY) = the instant at which the Nsukka/Yg clock reads TNLDY (clock.py)

The clock reads time from Nsukka on the engine's own year, Yg: a Yg year starts
on 1 December at 00:00 Nsukka time (WAT, UTC+01:00), its yeardays are real days
from there, and every Yg year is recalibrated. TNLDY 0 is then yearday 340 of
Yg 1969: 1969-11-06 00:00 Nsukka. At a recalibration after 365 civil days the
last 5/23 day of TNLDY is passed over (no instant); after 366 the first 18/23
day of the next is met twice (two instants, the first taken as the date).

The year unit is 8400/23 = 365.2174 days, which is what the 48.3/17640 factor in
the REVOTT expression reduces to: 48.3/17640 = 23/8400.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from fractions import Fraction as F

from . import clock

# REVOTT's own zero, in TNLDY. Y = 0, X = 0.
REVOTT_ZTP = F(14160)

# One unit of Y or X is this many TNLDY.
UNIT_DAYS = F(100)

# The year unit. 48.3/17640 == 23/8400 == 1 / (8400/23).
PER_YEAR = F(23, 8400)
YEAR_DAYS = F(8400, 23)

# year = TNLDY × 23/8400 + YEAR_BASE, with YEAR_BASE = 5849 + 391/420 − 3880.
YEAR_BASE = F(5849) + F(391, 420) - F(3880)

# Nsukka's zone, in which every instant is read and shown.
NSUKKA = clock.WAT


def _f(value) -> F:
    """Exact rational from an int, float, str or Fraction."""
    if isinstance(value, F):
        return value
    if isinstance(value, int):
        return F(value)
    return F(str(value))


def tnldy(y=0, x=0) -> F:
    """The TNLDY of position X in the instance shifted by Y."""
    return REVOTT_ZTP + UNIT_DAYS * _f(y) + UNIT_DAYS * _f(x)


def ztp_of(y=0) -> F:
    """The instance's own Ztp, in TNLDY. X = 0."""
    return tnldy(y, 0)


def year_of(y=0, x=0, t: F | None = None) -> F:
    """The decimal year, exactly. Pass either (y, x) or a TNLDY directly."""
    t = tnldy(y, x) if t is None else _f(t)
    return t * PER_YEAR + YEAR_BASE


def _instant(ms: F) -> datetime:
    """Epoch milliseconds (exact) as a datetime in Nsukka time, to the microsecond."""
    return (clock.UNIX + timedelta(microseconds=round(ms * 1000))).astimezone(NSUKKA)


def instants_of(y=0, x=0, t: F | None = None) -> list[datetime]:
    """Every instant at which the clock reads this TNLDY, in Nsukka time: none where a
    recalibration passes it over, two where one meets it twice, otherwise one."""
    t = tnldy(y, x) if t is None else _f(t)
    return [_instant(ms) for ms in clock.instants(t)]


def date_of(y=0, x=0, t: F | None = None) -> datetime | None:
    """The instant, in Nsukka time: the first where there are two, None where there is none."""
    found = instants_of(y, x, t)
    return found[0] if found else None


def tnldy_at_date(when: datetime) -> F:
    """The TNLDY of a moment, exactly. A moment without a zone is Nsukka time."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=NSUKKA)
    d = when - clock.UNIX
    us = (d.days * 86400 + d.seconds) * 10**6 + d.microseconds
    ms = us // 1000
    return clock.z_of(ms) + F(us - ms * 1000, 86400 * 10**6)


def day_ordinal(t) -> int | None:
    """Nsukka's calendar day (proleptic ordinal) of TNLDY t's first instant; None where it has none."""
    when = date_of(t=t)
    return None if when is None else when.date().toordinal()


_TABLE = None


def day_ordinals(t):
    """day_ordinal over a numpy array of TNLDY values, -1 where a recalibration passes one over."""
    import numpy as np
    global _TABLE
    if _TABLE is None:
        years = np.arange(1900, 2161)
        _TABLE = (years,
                  np.array([float(clock.z_start(int(g))) for g in years]),
                  np.array([(clock.start_ms(int(g) + 1) - clock.start_ms(int(g))) // clock.DAY_MS for g in years]),
                  np.array([date(int(g) - 1, 12, 1).toordinal() for g in years]))
    years, zs, length, o0 = _TABLE
    t = np.asarray(t, dtype=float)
    i = (np.floor((t + 340.0) / float(YEAR_DAYS)).astype(np.int64) + 1969 - int(years[0]))
    i = np.where(t < zs[i], i - 1, i)
    i = np.where(t >= zs[i] + float(YEAR_DAYS), i + 1, i)
    yd = t - zs[i]
    out = o0[i] + np.floor(yd).astype(np.int64)
    out = np.where((length[i - 1] == 366) & (yd < 366 - float(YEAR_DAYS)), o0[i - 1] + 365, out)
    return np.where((length[i] == 365) & (yd >= 365), -1, out)


def x_at_date(when: datetime, y=0) -> F:
    """Which X lands on this moment, in the instance shifted by Y."""
    return (tnldy_at_date(when) - REVOTT_ZTP) / UNIT_DAYS - _f(y)


def y_for_ztp(year) -> F:
    """The Y whose instance Ztp falls on this decimal year."""
    return ((_f(year) - YEAR_BASE) / PER_YEAR - REVOTT_ZTP) / UNIT_DAYS


def expression(y=0, x=0) -> str:
    """The REVOTT expression as written, for a given Y and X."""
    return (f"(((((100)×(({y})+(0)))+(100×(({x})+(0÷35)))+(((14160))+(0÷7)))"
            f"×(48.3÷17640))+5849+(391÷420)−3880)")
