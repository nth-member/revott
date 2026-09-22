#!/usr/bin/env python3
"""Turn the daily aggregate into the scalar field a path can be scored against.

Nothing raw. The series grows by two orders of magnitude across fifty years,
changes what it measures at 2013-04-01, and carries a weekly cycle that is 70%
of its residual variance. Three corrections, in order:

  1. level      log10 volume minus a centred 91-day rolling median.
                Removes the growth and the collection step changes, which are
                artefacts of GDELT's history rather than the world's.

  2. weekday    minus a day-of-week offset estimated on a centred 365-day
                window. Saturday and Sunday run at 0.57-0.69x a Wednesday and
                the ratio drifts across the decades, so the offset is local,
                not global.

                This one is not cosmetic. One unit of X is 100 days and
                100 = 2 (mod 7), so positions inside an instance walk the week
                with period 7; and one step of Y at day resolution moves every
                position by exactly one weekday. An uncorrected sweep over Y
                therefore carries a period-7 ripple that is entirely the
                working week, and "is this position a local maximum" would
                largely mean "is this a Wednesday".

  3. annual     minus a day-of-year offset estimated from the same calendar
                position in the surrounding +/-5 years. Without it the news
                year's own shape stays in the residual and dominates its tails:
                Jan 1 averages z = -4.0 and Dec 25 z = -3.6, every year, and
                the day-of-year means carry 47% of the residual sd -- two
                thirds of the weekday effect's size and far more concentrated.

                A centred 91-day median cannot absorb this. It straddles the
                holiday fortnight with eleven normal weeks, so a sharp two-week
                collapse survives it almost intact.

                Like the weekday, it aliases the sweep: a Y step of 0.01 is one
                day, so the path's day-of-year rotates with it, at period
                365.2425 days = 3.6524 in Y.

  4. scale      divided by a centred 365-day sd of the corrected residual, so
                that eras of differing noisiness compare. The 2006-2013.3
                monthly era is ~1.8x noisier than the 1979-2005 yearly one.

NULL days stay NULL throughout. They are never zero and never interpolated.
"""
import csv, sys
import numpy as np
from datetime import date

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else SRC

rows = list(csv.DictReader(open(SRC)))
d = np.array([date(*map(int, r["date"].split("-"))) for r in rows])
present = np.array([r["present"] == "1" for r in rows])
v = np.array([int(r["n_events"]) if r["present"] == "1" else 0 for r in rows], float)

lg = np.where(present & (v > 0), np.log10(np.where(v > 0, v, 1)), np.nan)
dow = np.array([x.weekday() for x in d])
n = len(lg)


def centred(arr, width, fn, minobs):
    out = np.full(n, np.nan)
    h = width // 2
    for i in range(n):
        w = arr[max(0, i - h): i + h + 1]
        w = w[~np.isnan(w)]
        if len(w) >= minobs:
            out[i] = fn(w)
    return out


# 1. level
level = centred(lg, 91, np.median, 30)
r1 = lg - level

# 2. weekday, local
dow_adj = np.full(n, np.nan)
h = 182
for i in range(n):
    lo, hi = max(0, i - h), min(n, i + h + 1)
    w = r1[lo:hi][dow[lo:hi] == dow[i]]
    w = w[~np.isnan(w)]
    if len(w) >= 12:
        dow_adj[i] = np.median(w)
r2 = r1 - dow_adj

# 3. annual, local.  Matched on the exact calendar date rather than on a
# day offset: the sharpest days of the year -- Jan 1, Dec 25 -- are one day
# deep, and a window even +/-3 days wide smears them into their neighbours and
# leaves them half corrected.
ann = np.full(n, np.nan)
md = {}
for i, x in enumerate(d):
    md.setdefault((x.month, x.day), []).append(i)
years = np.array([x.year for x in d])
for i, x in enumerate(d):
    for widen in (0, 1, 2):
        idx = []
        for dd in range(-widen, widen + 1):
            o = x.toordinal() + dd
            key = (date.fromordinal(o).month, date.fromordinal(o).day)
            idx.extend(md.get(key, []))
        idx = np.array(idx, int)
        idx = idx[np.abs(years[idx] - x.year) <= 8]
        w = r2[idx]
        w = w[~np.isnan(w)]
        if len(w) >= 8:
            ann[i] = np.median(w)
            break
r3 = r2 - ann

# 4. scale, local
scale = centred(r3, 365, lambda w: w.std(), 120)
z = r3 / scale

FIELDS = list(rows[0].keys())
for c in ("level_log10", "dow_adj", "ann_adj", "resid", "scale", "z"):
    if c not in FIELDS:
        FIELDS.append(c)


def fmt(x):
    return "" if np.isnan(x) else f"{x:.6f}"


with open(OUT, "w", newline="") as fh:
    w_ = csv.DictWriter(fh, FIELDS)
    w_.writeheader()
    for i, r in enumerate(rows):
        r.update(level_log10=fmt(level[i]), dow_adj=fmt(dow_adj[i]),
                 ann_adj=fmt(ann[i]), resid=fmt(r3[i]), scale=fmt(scale[i]),
                 z=fmt(z[i]))
        w_.writerow(r)

ok = ~np.isnan(z)
print(f"wrote {OUT}")
print(f"  z defined on {ok.sum()} of {n} days")
print(f"  z  mean={np.nanmean(z):+.4f}  sd={np.nanstd(z):.4f}  "
      f"min={np.nanmin(z):+.2f}  max={np.nanmax(z):+.2f}")
print("\n  residual sd, before and after the weekday correction:")
for lab, lo, hi in [("1979-2005 yearly", date(1979,1,1), date(2005,12,31)),
                    ("2006-2013.3 monthly", date(2006,1,1), date(2013,3,31)),
                    ("2013.4-2015.2 daily", date(2013,4,1), date(2015,2,18)),
                    ("2015.2- daily", date(2015,2,19), date(2026,9,20))]:
    m = (d >= lo) & (d <= hi)
    a, b = np.nanstd(r1[m]), np.nanstd(r2[m])
    print(f"    {lab:<22} {a:.4f} -> {b:.4f}   ({1-b/a:.0%} removed)")
print("\n  residual weekday means after correction (should be ~0):")
print("   ", "  ".join(f"{nm}={np.nanmean(r3[dow==k]):+.4f}"
                       for k, nm in enumerate("Mon Tue Wed Thu Fri Sat Sun".split())))
doy = np.array([x.timetuple().tm_yday for x in d])
for lab, arr in (("before", r2), ("after ", r3)):
    mm = np.array([np.nanmean(arr[doy == k]) for k in range(1, 367)])
    print(f"  day-of-year means {lab} the annual correction: "
          f"sd {np.nanstd(mm):.4f}, min {np.nanmin(mm):+.3f} (doy "
          f"{int(np.nanargmin(mm))+1}), max {np.nanmax(mm):+.3f}")
