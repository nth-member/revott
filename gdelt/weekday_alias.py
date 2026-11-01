#!/usr/bin/env python3
"""How large is the weekday artefact, for each candidate statistic, exactly.

Run:  python3 weekday_alias.py

THE UNITS OF X are the 401 SFO-BB node values. They are irregular -- 262
distinct gaps, the tightest 0.09 days, the most common 10.8 days, with 252-day
jumps through the set -- so there is no fixed step in X and no argument about
the sweep can be built on one.

THE ALIASING IS ON THE Y SIDE, and it is exact. One step of Y at day resolution
is 0.01 = one day, which shifts every node on the path by one day at once. The
weekday of the whole path therefore rotates together with period 7 days, i.e.
period 0.07 in Y, and any statistic averaging the field over the path carries an
exactly period-7 component in Y fixed by one thing: the path's weekday
histogram. That histogram is not flat -- the node values were not chosen against
a calendar -- and the artefact follows from it.

This file computes, for each candidate statistic, the ripple across the 7
rotations against that statistic's own noise floor. It needs no field data: only
the calendar, the DAG, and the weekday offsets measured by field.py.

WHAT IT SHOWS. The mean gradient over the backbone appears immune. It is not
robust, it is empty: the backbone visits all 401 nodes in order, so a mean
gradient over it telescopes to (f(sink) - f(root))/400 for ANY f. Every
statistic that carries information -- |gradient|, sign changes, monotone runs,
anything over the 307 long-range edges -- is exposed, between 2.3x and 4.3x.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from revott.core import day_ordinals
from revott.sfo import SFO

NAMES = "Mon Tue Wed Thu Fri Sat Sun".split()
# Weekday offsets in log10 residual units, and the residual sd, both as
# measured by field.py step 1 over the whole series.
OFFSET = np.array([-0.0074, +0.0286, +0.0339, +0.0292, +0.0041, -0.1642, -0.1830])
RESID_SD = 0.1254



def weekday(y, xs):
    """Nsukka's weekday of each X in the instance shifted by Y, on the Nsukka/Yg clock;
    -1 where a recalibration passes a node over."""
    # +6 because ordinal 1 (0001-01-01) is a Monday, so that Mon=0 as in
    # datetime.weekday(), which is how OFFSET is indexed.
    o = day_ordinals(np.round(14160.0 + 100.0 * y + 100.0 * np.asarray(xs), 4))
    return np.where(o < 0, -1, (o + 6) % 7)


def ripple(values_by_rotation, noise_floor):
    v = np.asarray(values_by_rotation) / RESID_SD
    r = v.max() - v.min()
    return r, r / noise_floor


def report(sfo, y):
    xs = np.array(sfo.order)
    wn = weekday(y, xs)
    wn = wn[wn >= 0]                       # nodes passed over at a Yg recalibration have no day
    c = Counter(wn.tolist())
    print(f"\nY = {y}")
    print("  weekday histogram of the 400 nodes:  "
          + "  ".join(f"{NAMES[k]}={c.get(k, 0):>3}" for k in range(7))
          + f"   (flat would be {len(xs) / 7:.1f})")

    groups = [("mean z over nodes", None, sfo.order),
              ("mean gradient, backbone", sfo.backbone(), None),
              ("mean |gradient|, backbone", sfo.backbone(), None),
              ("mean |gradient|, long-range", sfo.long_range(), None),
              ("mean |gradient|, all edges", sfo.edges, None)]

    print(f"  {'statistic':<30}{'n':>5}{'ripple':>10}{'floor':>9}{'ratio':>8}")
    for label, edges, nodes in groups:
        if nodes is not None:
            n = len(wn)
            vals = [OFFSET[(wn + k) % 7].mean() for k in range(7)]
            floor = 1 / np.sqrt(n)
        else:
            ws = weekday(y, [e.source for e in edges])
            wt = weekday(y, [e.target for e in edges])
            keep = (ws >= 0) & (wt >= 0)
            ws, wt, n = ws[keep], wt[keep], int(keep.sum())
            if label.startswith("mean gradient"):
                vals = [(OFFSET[(wt + k) % 7] - OFFSET[(ws + k) % 7]).mean()
                        for k in range(7)]
            else:
                vals = [np.abs(OFFSET[(wt + k) % 7] - OFFSET[(ws + k) % 7]).mean()
                        for k in range(7)]
            floor = np.sqrt(2 / n)
        r, ratio = ripple(vals, floor)
        flag = "   <- telescopes; empty" if label == "mean gradient, backbone" else ""
        print(f"  {label:<30}{n:>5}{r:>10.4f}{floor:>9.4f}{ratio:>7.1f}x{flag}")


if __name__ == "__main__":
    print(__doc__.strip())
    sfo = SFO()
    print("\n" + "=" * 66)
    print(f"DAG: {len(sfo)} nodes, {len(sfo.edges)} edges "
          f"({len(sfo.backbone())} backbone + {len(sfo.long_range())} long-range), "
          f"root {sfo.roots()[0]}, sink {sfo.sinks()[0]}")
    print("The backbone is exactly consecutive-in-x, so it orders the path the way")
    print("the calendar already does. The structure is the long-range edges.")
    for y in (24.50, 34.918, 82.80, 85.32):
        report(sfo, y)
    print("\n" + "=" * 66)
    print("Only the empty statistic is safe. Every informative one needs the")
    print("weekday correction, which is what field.py's `z` column carries.")
