"""The coordinate system.

Everything here is exact.  TNLDY is the coordinate; a calendar date and a
decimal year are two readings of it, and neither is primary.

    TNLDY(Y, X) = 14160 + 100·Y + 100·X
    year(TNLDY) = TNLDY × 23/8400 + 1969 + 391/420
    date(TNLDY) = 1969-11-07T11:28:41.739Z + TNLDY days

The year unit is 8400/23 = 365.2174 days, which is what the 48.3/17640 factor in
the REVOTT expression reduces to: 48.3/17640 = 23/8400.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fractions import Fraction as F

# REVOTT's own zero, in TNLDY. Y = 0, X = 0.
REVOTT_ZTP = F(14160)

# One unit of Y or X is this many TNLDY.
UNIT_DAYS = F(100)

# The year unit. 48.3/17640 == 23/8400 == 1 / (8400/23).
PER_YEAR = F(23, 8400)
YEAR_DAYS = F(8400, 23)

# year = TNLDY × 23/8400 + YEAR_BASE, with YEAR_BASE = 5849 + 391/420 − 3880.
YEAR_BASE = F(5849) + F(391, 420) - F(3880)

# TNLDY 0. Fixed by the corpus: every node satisfies TNLDY = 16610 + 100X at
# Y = 24.50, and position 0.00 there carries this instant.
TNLDY_ORIGIN = datetime(1969, 11, 7, 11, 28, 41, 739000, tzinfo=timezone.utc)


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


def date_of(y=0, x=0, t: F | None = None) -> datetime:
    """The instant, as a UTC datetime."""
    t = tnldy(y, x) if t is None else _f(t)
    return TNLDY_ORIGIN + timedelta(days=float(t))


def tnldy_at_date(when: datetime) -> F:
    """The TNLDY of a moment."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return F(str((when - TNLDY_ORIGIN).total_seconds() / 86400.0))


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
