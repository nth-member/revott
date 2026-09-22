#!/usr/bin/env python3
"""Plot the daily aggregate with its collection breakpoints marked.

The point is to see the corpus's own pathologies before scoring anything
through it: the series is not stationary, it grows by two orders of magnitude,
and it changes what it is measuring at 2013-04-01.
"""
import csv, sys
from datetime import date
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]

d, v, present = [], [], []
for r in csv.DictReader(open(SRC)):
    y, m, dd = map(int, r["date"].split("-"))
    d.append(date(y, m, dd))
    present.append(r["present"] == "1")
    v.append(int(r["n_events"]) if r["present"] == "1" else np.nan)
d = np.array(d); v = np.array(v, float); present = np.array(present)

# Rolling median in log space: the level drifts by 100x, so nothing raw.
lg = np.log10(np.where(v > 0, v, np.nan))
W = 91
base = np.full(len(lg), np.nan)
for i in range(len(lg)):
    w = lg[max(0, i - W // 2): i + W // 2 + 1]
    w = w[~np.isnan(w)]
    if len(w) >= W // 3:
        base[i] = np.median(w)
resid = lg - base

# Marked because each is a change in GDELT, not in the world. The 1996 and
# 2006 steps are larger than either of the two the handover named.
BREAKS = [(date(1996, 1, 1), "1996  source base\nwidens", -0.06),
          (date(2006, 1, 1), "2006  monthly\nfiles", -0.06),
          (date(2013, 4, 1), "2013-04  per-day files\nevent-date -> ingest-date", -0.06),
          (date(2015, 2, 19), "2015-02\nGDELT 2.0", 0.01)]
GAPS = [(date(2014, 1, 23), date(2014, 1, 25)), (date(2014, 3, 19), date(2014, 3, 19)),
        (date(2022, 11, 10), date(2022, 11, 10)), (date(2023, 3, 23), date(2023, 3, 23)),
        (date(2025, 6, 14), date(2025, 7, 1))]

fig, ax = plt.subplots(3, 1, figsize=(15, 10.5), sharex=True,
                       gridspec_kw={"height_ratios": [2, 1, 1], "hspace": 0.13})

ax[0].plot(d, v, lw=0.35, color="#1f4e79")
ax[0].plot(d, 10 ** base, lw=1.4, color="#d1495b", label=f"{W}-day rolling median")
ax[0].set_yscale("log"); ax[0].set_ylabel("events per day  (log)")
ax[0].set_title("GDELT daily event volume, 1979-01-01 .. 2026-09-20  "
                "— 17,430 days, 17,406 present, 24 NULL", loc="left", fontsize=12)
ax[0].legend(loc="upper left", fontsize=9, framealpha=0.9)

ax[1].axhline(0, color="#888", lw=0.8)
ax[1].plot(d, resid, lw=0.35, color="#2a6f4e")
ax[1].set_ylabel(f"log10 residual\nvs {W}-day median"); ax[1].set_ylim(-1.2, 1.2)

for a in ax:
    for t, _, _dx in BREAKS:
        a.axvline(t, color="#e07b39", lw=1.2, ls="--", zorder=0)
    for g0, g1 in GAPS:
        a.axvspan(g0, g1, color="#c0392b", alpha=0.28, lw=0, zorder=0)
for t, lab, dx in BREAKS:
    ax[0].annotate(lab, xy=(t, 0.02), xycoords=("data", "axes fraction"),
                   fontsize=8, color="#b35c1e",
                   ha="right" if dx < 0 else "left", va="bottom",
                   xytext=(-4 if dx < 0 else 4, 0), textcoords="offset points")
wd = np.array([x.weekday() for x in d])
for k, nm, col in [(6, "Sun", "#c0392b"), (5, "Sat", "#e07b39"), (2, "Wed", "#2a6f4e")]:
    m = wd == k
    yy = np.full(len(d), np.nan); yy[m] = resid[m]
    # 52-week running mean of that weekday's residual
    idx = np.where(m)[0]; vals = resid[idx]
    sm = np.array([np.nanmean(vals[max(0, j-26):j+27]) for j in range(len(idx))])
    ax[2].plot(d[idx], sm, lw=1.3, color=col, label=nm)
ax[2].axhline(0, color="#888", lw=0.8)
ax[2].set_ylabel("weekday offset\n(1-yr mean resid)")
ax[2].legend(loc="lower left", fontsize=8, ncol=3, framealpha=0.9)
ax[2].annotate("the weekly cycle — 70% of the residual sd.  One step of Y at day resolution moves every\n"
               "node by one weekday at once, so a sweep over Y ripples at period 7 — measured at\n"
               "0.217 z against a 0.050 z noise floor, 4.3x.  See weekday_alias.py.",
               xy=(0.43, 0.46), xycoords="axes fraction", fontsize=8.5, color="#333",
               bbox=dict(fc="white", ec="#ccc", boxstyle="round,pad=0.4", alpha=0.95))

ax[1].annotate("red bands: NULL days (no file published) — never read as zero",
               xy=(0.01, 0.06), xycoords="axes fraction", fontsize=8.5, color="#c0392b")
ax[2].xaxis.set_major_locator(mdates.YearLocator(5))
ax[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax[2].set_xlim(d[0], d[-1])
fig.savefig(OUT, dpi=140, bbox_inches="tight")
print("wrote", OUT)

print(f"\nresidual sd, by era:")
for lab, lo, hi in [("1979-2005 yearly files", date(1979,1,1), date(2005,12,31)),
                    ("2006-2013.3 monthly", date(2006,1,1), date(2013,3,31)),
                    ("2013.4-2015.2 daily 1.0", date(2013,4,1), date(2015,2,18)),
                    ("2015.2- daily 2.0", date(2015,2,19), date(2026,9,20))]:
    m = (d >= lo) & (d <= hi) & ~np.isnan(resid)
    print(f"  {lab:<26} n={m.sum():>5}  sd={np.nanstd(resid[m]):.4f}")
