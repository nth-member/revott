"""REVOTT — the Revelation Of The Trial coordinate system.

One coordinate, TNLDY, and two additive shifts on it:

    TNLDY = 14160 + 100·Y + 100·X

    14160   REVOTT's own Ztp
    100·Y   the per-instance shift; Y names the instance
    100·X   the position, free to range up and down the SFO

Everything else -- calendar dates, decimal years, the named readings -- is a
view of TNLDY.
"""

from .core import (
    REVOTT_ZTP,
    TNLDY_ORIGIN,
    UNIT_DAYS,
    YEAR_DAYS,
    date_of,
    tnldy,
    x_at_date,
    year_of,
    ztp_of,
)

__version__ = "0.1.0"
__all__ = [
    "REVOTT_ZTP", "TNLDY_ORIGIN", "UNIT_DAYS", "YEAR_DAYS",
    "tnldy", "date_of", "year_of", "ztp_of", "x_at_date",
]
