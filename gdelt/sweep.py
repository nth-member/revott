#!/usr/bin/env python3
"""Every anchoring, scored the same way, so a named one can be ranked.

    python3 sweep.py

Y at day resolution over [-147.60, 212.40] is 36,001 anchorings. The invariance
of §7 -- position X in instance Y falls on the same date as X' in Y' whenever
Y + X = Y' + X' -- means sliding Y is a shift of the whole path, so the sweep is
its own shift test and the null falls out of it.

COVERAGE. The path spans 36,000 days, 98.6 years. The field spans 47.7. No
anchoring can ever place all 400 nodes in the field, and the number it does
place runs from 1 to 384. Counts are therefore not comparable across
anchorings; rates are, and only among anchorings with enough nodes for a rate
to mean anything. This reports rank among anchorings covering at least 300
nodes, and prints how many those are.

The statistics are the ones overlay.py printed before any anchoring was
ranked. They are not chosen here.
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

HERE = Path(__file__).resolve().parent
MIN_COVER = 300
NAMED = (24.50, 34.918, 82.80, 85.32)

xs = np.array([k["x"] for k in json.loads((ROOT / "data" / "keys.json").read_text())["keys"]])
rows = list(csv.DictReader(open(HERE / "gdelt_daily_1979_2026.csv")))
LO = date(*map(int, rows[0]["date"].split("-"))).toordinal()
HI = date(*map(int, rows[-1]["date"].split("-"))).toordinal()
z = np.array([float(r["z"]) if r["z"] else np.nan for r in rows])

ok = ~np.isnan(z)
zs = np.sort(z[ok])
pct = np.full(len(z), np.nan)
pct[ok] = 100.0 * np.searchsorted(zs, z[ok], side="right") / len(zs)

ext = np.zeros(len(z), bool)
for i in np.where(ok)[0]:
    w = z[max(0, i - 3): i + 4]
    w = w[~np.isnan(w)]
    if len(w) >= 5 and (z[i] >= w.max() or z[i] <= w.min()):
        ext[i] = True

O = ORIGIN.toordinal() + (ORIGIN.hour * 3600 + ORIGIN.minute * 60
                          + ORIGIN.second + ORIGIN.microsecond / 1e6) / 86400.0
Ys = np.arange(-14760, 21241) / 100.0

STATS = ["mean_z", "rate_hi995", "rate_hi99", "rate_lo1", "rate_lo05", "rate_ext"]
res = {s: np.full(len(Ys), np.nan) for s in STATS}
cover = np.zeros(len(Ys), int)

for a in range(0, len(Ys), 2000):
    Yb = Ys[a:a + 2000]
    o = np.floor(O + 14160.0 + 100.0 * Yb[:, None] + 100.0 * xs[None, :]).astype(np.int64)
    inf = (o >= LO) & (o <= HI)
    idx = np.clip(o - LO, 0, len(z) - 1)
    zz = np.where(inf, z[idx], np.nan)
    pp = np.where(inf, pct[idx], np.nan)
    ee = np.where(inf & ~np.isnan(zz), ext[idx], False)
    n = (~np.isnan(zz)).sum(1)
    cover[a:a + 2000] = n
    with np.errstate(invalid="ignore", divide="ignore"):
        res["mean_z"][a:a + 2000] = np.nanmean(zz, 1)
        res["rate_hi995"][a:a + 2000] = (pp >= 99.5).sum(1) / n
        res["rate_hi99"][a:a + 2000] = (pp >= 99.0).sum(1) / n
        res["rate_lo1"][a:a + 2000] = (pp <= 1.0).sum(1) / n
        res["rate_lo05"][a:a + 2000] = (pp <= 0.5).sum(1) / n
        res["rate_ext"][a:a + 2000] = ee.sum(1) / n

adm = cover >= MIN_COVER
print(f"coverage: min {cover.min()}, max {cover.max()}, median {int(np.median(cover))}")
print(f"anchorings covering >= {MIN_COVER} nodes: {adm.sum():,} of {len(Ys):,}"
      f"   (Y from {Ys[adm].min():.2f} to {Ys[adm].max():.2f})\n")

hdr = f"{'Y':>9}{'cover':>7}" + "".join(f"{s:>22}" for s in STATS)
print(hdr); print("-" * len(hdr))
for Y in NAMED:
    i = int(round((Y + 147.60) * 100))
    line = f"{Y:>9}{cover[i]:>7}"
    for s in STATS:
        v = res[s][i]
        if not adm[i] or np.isnan(v):
            line += f"{'  (coverage too low)':>22}"
        else:
            better = (res[s][adm] >= v).sum()
            line += f"{v:>10.4f}{f'  #{better}/{adm.sum()}':>12}"
    print(line)
print("\nrank is by that statistic alone, high first, among admissible anchorings.")
print("A rank near the middle is the honest reading of a null result.")

np.savez(HERE / "sweep.npz", Ys=Ys, cover=cover, **res)
print(f"\nwrote sweep.npz  ({len(Ys):,} anchorings x {len(STATS)} statistics)")
