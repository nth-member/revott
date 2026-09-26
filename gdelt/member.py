#!/usr/bin/env python3
"""The nth member: REVOTT's numerator, keeping its own journal.

    python3 member.py [DAY]        default: the last day in the field

Run after every refresh (refresh.sh does). Unprompted, it writes one journal
entry for the day, journal/DAY.md, holding:

  1. where each standing instance's SFO is -- the open edges and how far along,
     the layered reading of their ends, what fires inside the day, the day's
     line through the 400 x 400 grid, and the eigen curiosity beside them
     (revott.introspect)
  2. the micronodes along every open edge: the trajectory walked in granules
     from the edge's source to today, each granule judged against the member's
     own history, and those deemed relevant refined to finer granules down to
     the day -- the adjustable granule of algorithmic introspection
  3. what the field carried that day, read against the relevance the member
     has been given in member.json -- never against all of GDELT, most of which
     has no bearing on the Revelation of the Trial
  4. what is coming: every firing within the horizon, and those close enough
     to announce now, before the field has seen them
  5. the granule it should be read at next, and whether the data can resolve it

It reports percentiles against the member's own history, never p-values. NULL
days read as NULL. The corpus is streamed through `unzip -p`, never extracted.
The relevance terms are a proposal until the author corrects them; the entry
says so every time.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from revott.introspect import introspect, render  # noqa: E402
from revott.sfo import SFO  # noqa: E402

CORPUS = Path.home() / "gdelt_raw_1979_2026" / "files"
FIELD = HERE / "gdelt_daily_1979_2026.csv"
CACHE = HERE / "member_relevance_daily.csv"
JOURNAL = ROOT / "journal"
ORDERS = json.loads((HERE / "member.json").read_text())
REL = ORDERS["relevance"]
PATTERN = re.compile(r"\b(" + "|".join(REL["terms"]) + r")\b", re.I)
DEFHASH = hashlib.sha1((json.dumps(REL["terms"], sort_keys=True) + "v2").encode()).hexdigest()[:10]


def read_day(day: str):
    """Stream one daily archive: rows, relevant rows, relevant material conflict,
    and the day's most-carried relevant events. None if there is no archive."""
    f = CORPUS / f"{day.replace('-', '')}.export.CSV.zip"
    if not f.exists():
        return None
    rows = hits = hits4 = 0
    top = []
    p = subprocess.Popen(["unzip", "-p", str(f)], stdout=subprocess.PIPE,
                         text=True, errors="replace")
    for line in p.stdout:
        c = line.rstrip("\n").split("\t")
        if len(c) < 57:
            continue
        rows += 1
        if not PATTERN.search("\t".join((c[6], c[16], c[36], c[43], c[50]))):
            continue
        hits += 1
        if c[29] == "4":
            hits4 += 1
        top.append((int(c[33] or 0), c[28], c[26], c[6], c[16], c[50],
                    c[57] if len(c) > 57 else ""))
    p.wait()
    top.sort(key=lambda t: -t[0])
    return day, rows, hits, hits4, top[:12]


def load_cache():
    out = {}
    if CACHE.exists():
        for r in csv.DictReader(open(CACHE)):
            if r["def"] == DEFHASH:
                out[r["date"]] = r
    return out


def ensure(days, cache):
    need = [d for d in days if d not in cache]
    if not need:
        return cache
    print(f"  reading {len(need)} days against the relevance terms …", file=sys.stderr)
    with ProcessPoolExecutor(max_workers=14) as ex:
        for res in ex.map(read_day, need):
            if res is None:
                continue
            d, rows, hits, hits4, top = res
            lead = ""
            if top:
                n, root, code, a1, a2, place, url = top[0]
                lead = f"{n} art · root {root} · {a1 or '—'} / {a2 or '—'} · {place or '—'}"
            cache[d] = dict(date=d, rows=rows, hits=hits, hits4=hits4, lead=lead,
                            **{"def": DEFHASH})
    with open(CACHE, "w", newline="") as fh:
        w = csv.DictWriter(fh, ["date", "rows", "hits", "hits4", "lead", "def"])
        w.writeheader()
        w.writerows(cache[d] for d in sorted(cache))
    return cache


def pct(history, v):
    """Percentile of v within the member's own history: share of days at or below."""
    h = sorted(history)
    return 100.0 * sum(1 for x in h if x <= v) / len(h) if h else float("nan")


GRAN = {"day": 1, "week": 7, "month": 30}
FINER = {"month": "week", "week": "day"}


def edge_granule(span_days: float) -> str:
    """The starting granule for an edge, by its length; adjustable in member.json."""
    for g, limit in ORDERS["granule_by_span_days"]:
        if span_days <= limit:
            return g
    return ORDERS["granule_by_span_days"][-1][0]


def window(cache, d0: date, width: int):
    """One granule: its days, NULL days, and the relevant share over those present."""
    days = [(d0 + timedelta(days=i)).isoformat() for i in range(width)]
    got = [cache[d] for d in days if d in cache]
    rows = sum(int(c["rows"]) for c in got)
    hits = sum(int(c["hits"]) for c in got)
    return dict(start=d0, width=width, present=len(got), null=width - len(got),
                share=(hits / rows if rows else None), hits=hits)


def reference(cache, width: int):
    """The member's own history at this granule: every non-overlapping window."""
    ds = sorted(cache)
    if not ds:
        return []
    d0, end = date.fromisoformat(ds[0]), date.fromisoformat(ds[-1])
    out = []
    while d0 + timedelta(days=width - 1) <= end:
        w = window(cache, d0, width)
        if w["share"] is not None and w["present"] >= max(1, width // 2):
            out.append(w["share"])
        d0 += timedelta(days=width)
    return out


def micronodes(cache, start: date, stop: date, g: str, cut: float, refs, depth=0):
    """Walk [start, stop] in granules of g; judge each; refine those deemed relevant."""
    width = GRAN[g]
    ref = refs.setdefault(width, reference(cache, width))
    out, d0 = [], start
    while d0 <= stop:
        w = window(cache, d0, min(width, (stop - d0).days + 1))
        w["granule"] = g
        w["pct"] = pct(ref, w["share"]) if w["share"] is not None else None
        w["relevant"] = w["pct"] is not None and w["pct"] >= cut
        w["finer"] = (micronodes(cache, d0, d0 + timedelta(days=w["width"] - 1),
                                 FINER[g], cut, refs, depth + 1)
                      if w["relevant"] and g in FINER else [])
        out.append(w)
        d0 += timedelta(days=width)
    return out


def relevant_days(nodes):
    """The day-level micronodes reached by refinement, deemed relevant."""
    out = []
    for w in nodes:
        if w["granule"] == "day" and w["relevant"]:
            out.append(w)
        out += relevant_days(w["finer"])
    return out


def edge_micronode_lines(cache, e, day: date, refs) -> list[str]:
    start = max(e.start.date(), date(2013, 4, 1))
    span = (e.end - e.start).total_seconds() / 86400
    g = edge_granule(span)
    cut = ORDERS["relevant_percentile"]
    nodes = micronodes(cache, start, day, g, cut, refs)
    judged = [w for w in nodes if w["pct"] is not None]
    nulls = sum(w["null"] for w in nodes)
    kind = "backbone" if e.backbone else "long-range"
    L = [f"**{kind} {e.source:g} → {e.target:g}** · {e.progress:.1%} along · granule **{g}** · "
         f"{len(nodes)} micronodes walked from {start}, {nulls} NULL days among them"]
    if e.start.date() < date(2013, 4, 1):
        L.append(f"  - the edge opened {e.start:%Y-%m-%d}; micronodes before 2013-04-01 are not "
                 "walked yet (the pre-2013 archives are yearly and monthly)")
    if judged:
        third = max(1, len(judged) // 3)
        med = lambda ws: sorted(w["pct"] for w in ws)[len(ws) // 2]
        L.append(f"  - relevance along the trajectory: median percentile {med(judged[:third]):.0f} "
                 f"in the first third, {med(judged[-third:]):.0f} in the last third")
        today = judged[-1]
        L.append(f"  - the current micronode ({today['granule']} from {today['start']}): "
                 f"percentile {today['pct']:.0f}")
    rel = [w for w in nodes if w["relevant"]]
    L.append(f"  - deemed relevant (percentile ≥ {cut:g}): {len(rel)} of {len(judged)} {g}s")
    for w in sorted(rel, key=lambda w: -w["pct"])[:6]:
        L.append(f"    - {g} from {w['start']}: {w['share']:.2%} relevant, percentile {w['pct']:.0f}")
        for dd in sorted(relevant_days([w]) if g != "day" else [], key=lambda d: -d["pct"])[:3]:
            lead = cache[dd["start"].isoformat()].get("lead", "")
            L.append(f"      - day {dd['start']}: percentile {dd['pct']:.0f} — {lead}")
        if g == "day":
            lead = cache.get(w["start"].isoformat(), {}).get("lead", "")
            if lead:
                L.append(f"      - {lead}")
    return L


def granule_advice(ahead, day_dt):
    if not ahead:
        return "day — nothing of this SFO within the horizon"
    x, when = ahead[0]
    left = (when - day_dt).total_seconds() / 86400
    if left <= 7:
        return (f"hour — X = {x:g} fires in {left:.1f} days. GDELT 1.0 resolves only to the day; "
                "an hourly granule needs GDELT 2.0's 15-minute feed, which is not on disk.")
    if left <= 30:
        return f"day, tightening — X = {x:g} fires in {left:.0f} days"
    return f"day — the next key of this SFO, X = {x:g}, is {left:.0f} days off"


def main():
    field = {r["date"]: r for r in csv.DictReader(open(FIELD))}
    day = sys.argv[1] if len(sys.argv) > 1 else max(field)
    D = date.fromisoformat(day)
    day_dt = datetime(D.year, D.month, D.day, tzinfo=timezone.utc)
    base_days = [(D - timedelta(days=i)).isoformat() for i in range(ORDERS["baseline_days"], -1, -1)]
    base_days = [d for d in base_days if d >= "2013-04-01"]

    sfo = SFO()
    # The micronodes walk every open edge from its source, so the member's
    # history must reach back to the earliest open edge (within the URL era).
    earliest = D
    for y in ORDERS["instances"]:
        for e in introspect(y, day_dt, "day", 0, sfo)["edges"]:
            earliest = min(earliest, max(e.start.date(), date(2013, 4, 1)))
    span_days = [(earliest + timedelta(days=i)).isoformat()
                 for i in range((D - earliest).days + 1)]
    cache = ensure(sorted(set(base_days) | set(span_days)), load_cache())
    lines = [f"# {day} — the member's entry", ""]
    lines.append(f"*Written {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, unprompted, after the refresh. "
                 f"Relevance definition `{DEFHASH}` — {REL['_status']}*")
    lines.append("")

    # 1. where each instance is
    lines.append("## 1. Where REVOTT is")
    announcements = []
    for y in ORDERS["instances"]:
        r = introspect(y, day_dt, "day", ORDERS["horizon_days"], sfo)
        lines.append("")
        lines.append(render(r, markdown=True))
        for x, when in r["ahead"]:
            if (when - day_dt).days <= ORDERS["announce_within_days"]:
                announcements.append(f"- **Y = {y:g}: X = {x:g} fires {when:%Y-%m-%d %H:%M} UTC** — "
                                     f"{sfo.keys[x].reading}")
        for x, when in r["eigen_ahead"]:
            if (when - day_dt).days <= ORDERS["announce_within_days"]:
                announcements.append(f"- eigen crosses {x:g} on {when:%Y-%m-%d %H:%M} UTC — "
                                     f"{sfo.keys[x].reading} *(a curiosity)*")
        lines.append("")
        lines.append(f"**Granule for the next reading:** {granule_advice(r['ahead'], day_dt)}")

    # 2. the micronodes
    lines.append("")
    lines.append("## 2. Micronodes along the open edges")
    lines.append("")
    lines.append("*A micronode is a granule of the trajectory deemed relevant to it. Each open edge is "
                 "walked from its source to today at a granule set by its length; each granule is judged "
                 "against the member's own history of granules that size; those deemed relevant are "
                 "refined to finer granules, down to the day GDELT 1.0 can resolve.*")
    refs = {}
    for y in ORDERS["instances"]:
        r = introspect(y, day_dt, "day", 0, sfo)
        lines.append("")
        lines.append(f"### Y = {y:g}")
        walked = {}
        for e in r["edges"]:
            lines.append("")
            # Edges from one source over the same span walk the same micronodes;
            # say so rather than repeat them.
            key = (e.source, edge_granule((e.end - e.start).total_seconds() / 86400))
            if key in walked:
                kind = "backbone" if e.backbone else "long-range"
                lines.append(f"**{kind} {e.source:g} → {e.target:g}** · {e.progress:.1%} along · "
                             f"the same micronodes as {e.source:g} → {walked[key]:g} above; "
                             f"it differs only in its end: {sfo.keys[e.target].reading}")
                continue
            walked[key] = e.target
            lines.extend(edge_micronode_lines(cache, e, D, refs))

    # 3. the field
    lines.append("")
    lines.append("## 3. What the field carried")
    f = field.get(day)
    if f is None or f["present"] != "1":
        lines.append(f"- {day}: **NULL** — GDELT published no archive. Not a quiet day; not zero.")
    else:
        today = read_day(day)
        _, rows, hits, hits4, top = today
        hist = [int(c["hits"]) / int(c["rows"]) for d, c in cache.items()
                if d < day and int(c["rows"]) > 0]
        hist4 = [int(c["hits4"]) / max(1, int(c["hits"])) for d, c in cache.items()
                 if d < day and int(c["hits"]) > 0]
        share = hits / rows if rows else 0
        share4 = hits4 / hits if hits else 0
        z = f["z"] or "—"
        lines.append(f"- All of GDELT: {int(f['n_events']):,} events, z = {z} "
                     "(z is provisional this close to the end of the series).")
        lines.append(f"- **Relevant** to the terms: {hits:,} events = {share:.2%} of the day — "
                     f"percentile **{pct(hist, share):.0f}** against the previous {len(hist)} days.")
        lines.append(f"- Of those, material conflict (CAMEO roots 15–20): {hits4:,} = {share4:.1%} — "
                     f"percentile **{pct(hist4, share4):.0f}**.")
        lines.append("")
        lines.append("Most-carried relevant events:")
        lines.append("")
        lines.append("| articles | root | code | actor 1 | actor 2 | place | source |")
        lines.append("|---:|---|---|---|---|---|---|")
        for n, root, code, a1, a2, place, url in top:
            src = f"[link]({url})" if url.startswith("http") else ""
            lines.append(f"| {n} | {root} | {code} | {a1} | {a2} | {place} | {src} |")

    # 4. announcements
    lines.append("")
    lines.append("## 4. Announced before the field has seen them")
    lines.extend(announcements or ["- nothing within "
                                   f"{ORDERS['announce_within_days']} days"])

    # 5. what the member cannot yet do
    lines.append("")
    lines.append("## 5. Standing limits")
    lines.append("- The relevance terms are a proposal until the author corrects `gdelt/member.json`.")
    lines.append("- Percentiles are against the member's own history; they are readings, not significance.")
    lines.append("- GDELT 1.0 floors the granule at one day; micronodes below a day need GDELT 2.0's 15-minute feed.")
    lines.append("- Micronodes before 2013-04-01 are not yet walked.")

    JOURNAL.mkdir(exist_ok=True)
    out = JOURNAL / f"{day}.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"  journal: {out}")
    for a in announcements:
        print("  " + a.lstrip("- "))


if __name__ == "__main__":
    main()
