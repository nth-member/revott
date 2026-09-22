#!/usr/bin/env python3
"""Merge per-file partials into one row per calendar day.

Reads the TSV that agg_one.sh emits (one row per covered day) and writes a
dense daily series over the corpus range, so that a day with no row is visible
as such rather than silently absent.

Three states, and they are not the same thing:

    present=1, n_events>0   a file covers this day and carried events
    present=1, n_events=0   a file covers this day and carried none
    present=0, fields empty  no file covers this day

The third is the one that matters. GDELT's manifest lists 20221110 and 20230323
but its server 404s both; the days either side are present. Read as zero, each
would be the largest single-day collapse in the series, and any anchoring whose
positions landed there would score spectacularly on an artefact. They are NULL.
"""
import csv, sys
from datetime import date, timedelta

PARTIALS, OUT = sys.argv[1], sys.argv[2]

# Breakpoints in how the corpus was collected, not in the world.
BREAKS = {
    date(2013, 4, 1): "daily-files",   # yearly/monthly SQLDATE -> per-ingestion-day files
    date(2015, 2, 19): "gdelt-2.0",    # 2.0 changeover
}

rows = {}
for ln in open(PARTIALS):
    f = ln.rstrip("\n").split("\t")
    d = date(int(f[0][:4]), int(f[0][4:6]), int(f[0][6:8]))
    n = int(f[3])
    rows[d] = dict(
        era="event-date" if f[1] == "sqldate" else "ingest-date",
        source=f[2], n_events=n,
        n_mentions=int(f[4]), n_articles=int(f[5]), n_sources=int(f[6]),
        avg_tone=(float(f[7]) / n) if n else "",
        avg_goldstein=(float(f[8]) / n) if n else "",
        n_root=int(f[9]),
        q1_verb_coop=int(f[10]), q2_mat_coop=int(f[11]),
        q3_verb_conf=int(f[12]), q4_mat_conf=int(f[13]),
        offday_rows=int(f[14]),
    )

lo, hi = min(rows), max(rows)
FIELDS = ["date", "present", "era", "n_events", "n_mentions", "n_articles",
          "n_sources", "avg_tone", "avg_goldstein", "n_root", "q1_verb_coop",
          "q2_mat_coop", "q3_verb_conf", "q4_mat_conf", "offday_rows",
          "breakpoint", "source"]

absent = []
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, FIELDS)
    w.writeheader()
    d, ndays = lo, 0
    while d <= hi:
        r = rows.get(d)
        if r is None:
            absent.append(d)
            w.writerow({"date": d, "present": 0, "breakpoint": BREAKS.get(d, "")})
        else:
            w.writerow({"date": d, "present": 1, "breakpoint": BREAKS.get(d, ""), **r})
        d += timedelta(days=1); ndays += 1

print(f"{lo} .. {hi}  {ndays} days  {ndays - len(absent)} present  {len(absent)} absent")
for d in absent:
    print(f"  absent: {d}")
