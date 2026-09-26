#!/usr/bin/env python3
"""REVOTT laid over GDELT, one row per node.

    python3 overlay.py [Y]          default Y = 24.50

For every one of the 400 SFO-BB nodes: the date it falls on in the instance
shifted by Y, what the field reads there, and where that reading sits in the
field's own distribution.

The reading is `z` from field.py -- log10 daily event volume, minus a centred
91-day median, minus a local day-of-week offset, over a local 365-day sd. The
percentile is against the empirical distribution of z over all 17,406 present
days, not against a normal, because the field's tails are heavier than normal
(z runs to -13.1).

`pct` is therefore directly readable: a node at pct 99.4 sits higher than 99.4%
of all days in fifty years. With N nodes covered, chance alone puts N/100 of
them above pct 99, so the expected counts printed with the summary are what any
single node has to be read against.

NULL days (§5a) are never scored. A node landing on one is reported as such.
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from revott.core import TNLDY_ORIGIN as ORIGIN
from revott.sfo import SFO

Y = float(sys.argv[1]) if len(sys.argv) > 1 else 24.50
FIELD = Path(__file__).resolve().parent / "gdelt_daily_1979_2026.csv"
WD = "Mon Tue Wed Thu Fri Sat Sun".split()

rows = list(csv.DictReader(open(FIELD)))
ordn = np.array([date(*map(int, r["date"].split("-"))).toordinal() for r in rows])
zval = np.array([float(r["z"]) if r["z"] else np.nan for r in rows])
nev = np.array([int(r["n_events"]) if r["present"] == "1" else -1 for r in rows])
present = np.array([r["present"] == "1" for r in rows])
LO, HI = ordn[0], ordn[-1]

# local extremum: the day is the max (or min) of z over a centred 7-day window
ok = ~np.isnan(zval)
ext = np.zeros(len(rows), np.int8)
for i in np.where(ok)[0]:
    w = zval[max(0, i - 3): i + 4]
    w = w[~np.isnan(w)]
    if len(w) >= 5:
        if zval[i] >= w.max(): ext[i] = 1
        elif zval[i] <= w.min(): ext[i] = -1

zsorted = np.sort(zval[ok])
def pct(z):
    return 100.0 * np.searchsorted(zsorted, z, side="right") / len(zsorted)

O = ORIGIN.toordinal() + (ORIGIN.hour * 3600 + ORIGIN.minute * 60
                          + ORIGIN.second + ORIGIN.microsecond / 1e6) / 86400.0
sfo = SFO()
out, covered = [], 0
for x in sfo.order:
    key = sfo.keys[x]
    t = 14160.0 + 100.0 * Y + 100.0 * x
    o = int(np.floor(O + t))
    d = date.fromordinal(o)
    rec = dict(x=x, tnldy=round(t, 4), date=d.isoformat(), weekday=WD[d.weekday()],
               in_field=int(LO <= o <= HI), present="", n_events="", z="", pct="",
               extremum="", out_degree=len(key.successors), carried=int(key.bare),
               text=key.reading)
    if LO <= o <= HI:
        i = o - LO
        rec["present"] = int(present[i])
        if present[i]:
            rec["n_events"] = int(nev[i])
        if not np.isnan(zval[i]):
            covered += 1
            rec["z"] = round(float(zval[i]), 4)
            rec["pct"] = round(float(pct(zval[i])), 2)
            rec["extremum"] = {1: "max", -1: "min", 0: ""}[int(ext[i])]
    out.append(rec)

dest = Path(__file__).resolve().parent / f"overlay_Y{Y:g}.csv".replace(".", "p", 1)
dest = Path(str(dest).replace("pcsv", ".csv"))
with open(dest, "w", newline="") as fh:
    w = csv.DictWriter(fh, list(out[0]))
    w.writeheader(); w.writerows(out)

zs = np.array([r["z"] for r in out if r["z"] != ""], float)
ps = np.array([r["pct"] for r in out if r["pct"] != ""], float)
print(f"REVOTT at Y = {Y}  over GDELT {rows[0]['date']} .. {rows[-1]['date']}")
print(f"  {covered} of 400 nodes scored; "
      f"{sum(1 for r in out if not r['in_field'])} outside the field, "
      f"{sum(1 for r in out if r['in_field'] and r['present'] == 0)} on NULL days")
print(f"  node z: mean {zs.mean():+.3f}  sd {zs.std():.3f}   "
      f"(field: mean {np.nanmean(zval):+.3f}  sd {np.nanstd(zval):.3f})")
print(f"\n  {'threshold':<14}{'nodes':>7}{'expected':>10}{'ratio':>8}")
for thr in (99.5, 99.0, 97.5, 95.0):
    n = int((ps >= thr).sum()); e = covered * (100 - thr) / 100
    print(f"  pct >= {thr:<8}{n:>7}{e:>10.1f}{n/e if e else 0:>7.2f}x")
for thr in (5.0, 2.5, 1.0, 0.5):
    n = int((ps <= thr).sum()); e = covered * thr / 100
    print(f"  pct <= {thr:<8}{n:>7}{e:>10.1f}{n/e if e else 0:>7.2f}x")
nx = sum(1 for r in out if r["extremum"])
base = (ext[ok] != 0).mean()
print(f"\n  local extrema: {nx} of {covered} = {nx/covered:.1%}   "
      f"field base rate {base:.1%}   ratio {(nx/covered)/base:.2f}x")
print(f"\nwrote {dest.name}")
