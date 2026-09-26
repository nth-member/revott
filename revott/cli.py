"""Command line.

    revott ztp                          REVOTT's own zero
    revott at --y 24.50 --x -147.6      one position in one instance
    revott sweep --y 24.50              every key of the SFO, dated in that instance
    revott sweep --y 24.50 --from -10 --to 10 --step 0.5    an arbitrary range of X
    revott instance --y 24.50           the instance's Ztp and span
    revott sfo                          the structure: keys, edges, anomalies
    revott readings --x 0.00            the named readings at a position
    revott page --y 24.50               build a page for the instance
    revott introspect --y 24.50 [--at 2026-10-05T00:00] [--granule day] [--ahead 90]
                                        where the instance's SFO is at an instant
"""

from __future__ import annotations

import argparse
import sys
from fractions import Fraction as F

from .core import (
    REVOTT_ZTP, TNLDY_ORIGIN, UNIT_DAYS, YEAR_DAYS,
    date_of, expression, tnldy, year_of, ztp_of,
)
from .sfo import SFO


def _row(y, x, key=None) -> str:
    t = tnldy(y, x)
    d = date_of(y, x)
    line = (f"{float(x):>10.4f}  TNLDY {float(t):>10.2f}  {d.date().isoformat()}  "
            f"{float(year_of(y, x)):>12.6f}")
    if key is not None:
        text = key.reading
        line += f"  {text[:58]}"
    return line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="revott", description="REVOTT: TNLDY = 14160 + 100Y + 100X")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ztp", help="REVOTT's own zero")

    p_at = sub.add_parser("at", help="one position in one instance")
    p_at.add_argument("--y", default="0")
    p_at.add_argument("--x", default="0")

    p_sw = sub.add_parser("sweep", help="X across the SFO for a fixed Y")
    p_sw.add_argument("--y", default="0")
    p_sw.add_argument("--from", dest="lo", default=None)
    p_sw.add_argument("--to", dest="hi", default=None)
    p_sw.add_argument("--step", default=None)
    p_sw.add_argument("--csv", action="store_true")

    p_in = sub.add_parser("instance", help="an instance's Ztp and span")
    p_in.add_argument("--y", default="0")

    sub.add_parser("sfo", help="the key structure and its anomalies")

    p_rd = sub.add_parser("readings", help="the named readings at a position")
    p_rd.add_argument("--x", default="0")

    p_is = sub.add_parser("introspect", help="where an instance's SFO is at an instant")
    p_is.add_argument("--y", default="24.50")
    p_is.add_argument("--at", default=None, help="ISO instant, UTC; default now")
    p_is.add_argument("--granule", default="day",
                      choices=["second", "minute", "hour", "day", "week", "month", "year"])
    p_is.add_argument("--ahead", type=int, default=90, help="horizon, days")

    p_pg = sub.add_parser("page", help="build an HTML page for an instance")
    p_pg.add_argument("--y", default="0")
    p_pg.add_argument("--title", default=None)
    p_pg.add_argument("--out", default=None)

    args = parser.parse_args(argv)

    if args.command == "introspect":
        from datetime import datetime, timezone
        from .introspect import introspect, render
        at = (datetime.fromisoformat(args.at) if args.at
              else datetime.now(timezone.utc))
        print(render(introspect(float(args.y), at, args.granule, args.ahead)))
        return 0

    if args.command == "ztp":
        print(f"REVOTT Ztp   : TNLDY {float(REVOTT_ZTP):,.0f}")
        print(f"  date       : {date_of(0, 0).isoformat()}")
        print(f"  year       : {float(year_of(0, 0)):.6f}")
        print(f"  expression : {expression(0, 0)}")
        print()
        print(f"TNLDY origin : {TNLDY_ORIGIN.isoformat()}  (TNLDY 0)")
        print(f"unit         : {float(UNIT_DAYS):.0f} TNLDY per unit of Y or X")
        print(f"year unit    : {YEAR_DAYS} = {float(YEAR_DAYS):.6f} days")
        return 0

    if args.command == "at":
        y, x = args.y, args.x
        sfo = SFO()
        t = tnldy(y, x)
        print(f"Y = {y}   X = {x}")
        print(f"  TNLDY      : {float(t):,.4f}   = 14160 + {float(F(str(y))*100):,.1f}"
              f" + {float(F(str(x))*100):,.1f}")
        print(f"  date       : {date_of(y, x).isoformat()}")
        print(f"  year       : {float(year_of(y, x)):.6f}")
        print(f"  instance   : Ztp TNLDY {float(ztp_of(y)):,.0f} = {date_of(y, 0).date()}")
        key = sfo.keys.get(float(x))
        if key:
            if key.strands:
                print(f"  key        : exact — {key.reading}")
            elif key.carried:
                print(f"  key        : exact — no text of its own")
                print(f"  standing   : {key.standing_text}")
                print(f"               carried from {key.carried_from}"
                      f" ({key.gap_to_carrier:+g} in position)")
            else:
                print(f"  key        : exact — no framework at or before this key")
            for edge in sfo.successors(key.x):
                mark = "" if edge.stated else "  [backbone, not written down]"
                print(f"     -> {edge.target}  gap {edge.gap}{mark}")
        else:
            near = sfo.nearest(float(x))
            print(f"  key        : none at this X; nearest at or before is {near.x}")
            print(f"               {near.text or '(no text on that key)'}")
        return 0

    if args.command == "instance":
        y = args.y
        sfo = SFO()
        lo, hi = sfo.span
        print(f"instance Y = {y}")
        print(f"  Ztp        : TNLDY {float(ztp_of(y)):,.0f}  =  {date_of(y, 0).isoformat()}")
        print(f"  shift      : {float(F(str(y)) * 100):,.0f} TNLDY off REVOTT's own zero")
        print(f"  year       : {float(year_of(y, 0)):.6f}")
        print(f"  SFO span   : X {lo} .. {hi}")
        print(f"               {date_of(y, lo).date()} .. {date_of(y, hi).date()}")
        print(f"  expression : {expression(y, 0)}")
        return 0

    if args.command == "sweep":
        y = args.y
        sfo = SFO()
        if args.lo is not None and args.hi is not None:
            step = F(str(args.step or 1))
            lo, hi = F(str(args.lo)), F(str(args.hi))
            xs, cur = [], lo
            while cur <= hi:
                xs.append(cur)
                cur += step
            keyed = [(x, sfo.keys.get(float(x))) for x in xs]
        else:
            keyed = [(F(str(k)), sfo.keys[k]) for k in sfo.order]
        if args.csv:
            print("x,tnldy,date,year,text")
            for x, key in keyed:
                text = (key.reading if key else "").replace('"', "'")
                print(f'{float(x)},{float(tnldy(y, x))},{date_of(y, x).date()},'
                      f'{float(year_of(y, x)):.6f},"{text}"')
        else:
            print(f"Y = {y}   Ztp TNLDY {float(ztp_of(y)):,.0f} = {date_of(y, 0).date()}"
                  f"   ({len(keyed)} positions)")
            print(f"{'X':>10}  {'TNLDY':>16}  {'date':>10}  {'year':>12}  framework")
            for x, key in keyed:
                print(_row(y, x, key))
        return 0

    if args.command == "sfo":
        sfo = SFO()
        lo, hi = sfo.span
        print(f"keys         : {len(sfo)}   X from {lo} to {hi}")
        print(f"relations    : {len(sfo.edges)}")
        print(f"  backbone   : {len(sfo.backbone())} — each key to the one immediately next")
        print(f"  long-range : {len(sfo.long_range())}")
        print(f"roots/sinks  : {sfo.roots()} / {sfo.sinks()}")
        print(f"bare keys    : {sum(1 for k in sfo.keys.values() if k.bare)} carry no text")
        implied = [e for e in sfo.edges if not e.stated]
        if implied:
            print(f"backbone links not written down: {len(implied)}")
            for e in implied:
                print(f"  {e.source} -> {e.target}  gap {e.gap}")
        if sfo.disputed():
            print(f"disputed gaps: {len(sfo.disputed())} — both numbers kept")
            for e in sfo.disputed():
                print(f"  {e.source} -> {e.target}  stated {e.gap}, positions imply {e.implied_gap}")
        for erratum in sfo.errata:
            print(f"erratum      : {erratum['id']} — {erratum['what']}")
        return 0

    if args.command == "readings":
        from . import readings as rd

        x = float(args.x)
        values = rd.at(x)
        if not values:
            print(f"no named readings recorded at X = {x}")
            print(f"({len(rd.covered())} positions carry them)")
            return 1
        print(f"named readings at X = {x}")
        for name in sorted(values):
            print(f"  {name:<36} {values[name]}")
        return 0

    if args.command == "page":
        from .page import build

        print(f"wrote {build(args.y, title=args.title, out=args.out)}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
