#!/usr/bin/env python3
"""Pack the daily aggregate and the SFO into what the app loads.

The app states one ratio per node:

    numerator    what the world recorded that day          n_events
    denominator  what that day would normally carry        10^(level + weekday + annual)
    ratio        numerator / denominator                   10^resid

The denominator is not a constant. It is the local level (91-day median in log
space), times the day's weekday factor, times its day-of-year factor -- the
three corrections field.py applies, recombined into the number they imply. A
ratio of 1.00 means the day was exactly ordinary for its moment, its weekday
and its season.
"""
import csv, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELD = HERE.parent / "gdelt" / "gdelt_daily_1979_2026.csv"
KEYS = HERE.parent / "data" / "keys.json"

rows = list(csv.DictReader(open(FIELD)))
ev, den, z = [], [], []
for r in rows:
    if r["present"] != "1" or not r["z"]:
        ev.append(-1); den.append(-1); z.append(None); continue
    n = int(r["n_events"])
    lg = float(r["level_log10"]) + float(r["dow_adj"] or 0) + float(r["ann_adj"] or 0)
    ev.append(n); den.append(round(10 ** lg)); z.append(round(float(r["z"]), 2))

field = {"start": rows[0]["date"], "end": rows[-1]["date"], "n": len(rows),
         "events": ev, "denom": den, "z": z}
(HERE / "data" / "field.json").write_text(json.dumps(field, separators=(",", ":")))

keys = json.loads(KEYS.read_text())["keys"]
nodes = [{"x": k["x"],
          "t": " || ".join(k["strands"]),
          "s": [[t, g] for t, g in k["successors"]]} for k in keys]
(HERE / "data" / "nodes.json").write_text(json.dumps(nodes, separators=(",", ":")))

for f in ("field.json", "nodes.json"):
    p = HERE / "data" / f
    print(f"  {f:<14} {p.stat().st_size/1024:8.1f} KB")
print(f"  field {field['start']} .. {field['end']}, {field['n']} days; {len(nodes)} nodes")
