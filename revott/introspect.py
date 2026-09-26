"""Where REVOTT is, at any instant: one micronode of introspection.

A micronode is a granule of time -- a second, an hour, a day, a year -- deemed
relevant to the developing SFO_BB -> SFO_BB trajectory. Its resolution is
adjustable. At each one this module answers, from the SFO alone:

    position     the instant's TNLDY, and the X it falls on in the instance Y
    firing       keys of the instance's SFO that fall inside the granule
    open edges   every edge in flight at the instant -- the backbone one and the
                 long-range spans over it -- with how far along each is, and the
                 layered reading of both its ends
    sentences    every (Y, X) pair of the 400 x 400 grid whose line falls inside
                 the granule, read as "X is being Y"
    eigen        Z = 200 Yp + 14160, the diagonal: one value at a time.
                 A curiosity -- the system's own stretched values -- reported
                 beside the primary readings, never in place of them
    ahead        the firings still to come in the instance, within a horizon

Each fixed Y generates its own 400-node, 704-edge SFO over X; Y names which one.
Nothing here reads GDELT. The field is read against this, not the other way round.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .core import REVOTT_ZTP, UNIT_DAYS, date_of, tnldy_at_date
from .sfo import SFO

GRANULES = {
    "second": timedelta(seconds=1), "minute": timedelta(minutes=1),
    "hour": timedelta(hours=1), "day": timedelta(days=1),
    "week": timedelta(days=7), "month": timedelta(days=30),
    "year": timedelta(days=365.2174),
}


@dataclass
class OpenEdge:
    source: float
    target: float
    backbone: bool
    start: datetime
    end: datetime
    progress: float
    source_reading: str
    target_reading: str


def _utc(when: datetime) -> datetime:
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def introspect(y: float, at: datetime, granule: str = "day",
               horizon_days: int = 90, sfo: SFO | None = None) -> dict:
    sfo = sfo or SFO()
    at = _utc(at)
    width = GRANULES[granule]
    lo, hi = at, at + width
    z = float(tnldy_at_date(at))
    x_now = (z - float(REVOTT_ZTP)) / float(UNIT_DAYS) - y
    when = {x: date_of(y, x) for x in sfo.order}

    firing = [x for x in sfo.order if lo <= when[x] < hi]

    edges = []
    for e in sfo.edges:
        a, b = when[e.source], when[e.target]
        if a <= at < b:
            edges.append(OpenEdge(e.source, e.target, e.default, a, b,
                                  (at - a) / (b - a),
                                  sfo.keys[e.source].reading,
                                  sfo.keys[e.target].reading))
    edges.sort(key=lambda o: (not o.backbone, o.end))

    # The granule's line through the 400 x 400 grid: every (Yi, Xj) whose date
    # falls inside it. Y + X fixes the date, so bound the sum and test only there.
    s_lo = (float(tnldy_at_date(lo)) - float(REVOTT_ZTP)) / float(UNIT_DAYS)
    s_hi = (float(tnldy_at_date(hi)) - float(REVOTT_ZTP)) / float(UNIT_DAYS)
    xs = sfo.order
    sentences = []
    for yi in xs:
        for xj in xs:
            if s_lo <= yi + xj < s_hi:
                sentences.append((yi, xj, date_of(yi, xj)))
    sentences.sort(key=lambda t: t[2])

    yp = (z - float(REVOTT_ZTP)) / 200.0
    nxt = next((x for x in xs if x > yp), None)
    prv = next((x for x in reversed(xs) if x <= yp), None)
    eigen = {"yp": yp, "last": prv, "next": nxt,
             "next_at": date_of(nxt, nxt) if nxt is not None else None}

    until = at + timedelta(days=horizon_days)
    ahead = [(x, when[x]) for x in xs if hi <= when[x] < until]
    eig_ahead = [(x, date_of(x, x)) for x in xs if hi <= date_of(x, x) < until]

    return dict(y=y, at=at, granule=granule, lo=lo, hi=hi, tnldy=z, x=x_now,
                firing=firing, edges=edges, sentences=sentences, eigen=eigen,
                ahead=ahead, eigen_ahead=eig_ahead, sfo=sfo)


def _short(text: str, n: int = 90) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def render(r: dict, markdown: bool = False) -> str:
    """The introspection as text; markdown=True for a journal entry."""
    sfo, y = r["sfo"], r["y"]
    out = []
    h = (lambda t: f"### {t}") if markdown else (lambda t: f"\n{t}\n" + "-" * len(t))
    out.append(f"REVOTT at Y = {y:g} · {r['at']:%Y-%m-%d %H:%M} UTC · granule: {r['granule']}")
    out.append(f"TNLDY {r['tnldy']:,.3f} · the instant falls on X = {r['x']:.4f} of this SFO")

    out.append(h("Firing inside the granule"))
    if r["firing"]:
        for x in r["firing"]:
            out.append(f"- X = {x:g} at {date_of(y, x):%H:%M} — {sfo.keys[x].reading}")
    else:
        out.append("- no key of this SFO falls inside the granule")

    out.append(h(f"Open edges ({len(r['edges'])})"))
    for e in r["edges"]:
        kind = "backbone" if e.backbone else "long-range"
        out.append(f"- {kind} {e.source:g} → {e.target:g} · {e.start:%Y-%m-%d} → "
                   f"{e.end:%Y-%m-%d} · {e.progress:.1%} along")
        out.append(f"    from: {_short(e.source_reading, 120)}")
        out.append(f"    to:   {_short(e.target_reading, 120)}")

    out.append(h(f"The granule's line through the grid ({len(r['sentences'])} sentences)"))
    for yi, xj, d in r["sentences"][:40]:
        out.append(f"- ({yi:g}, {xj:g}) {d:%H:%M} — «{_short(sfo.keys[xj].reading, 70)}» "
                   f"is being «{_short(sfo.keys[yi].reading, 60)}»")
    if len(r["sentences"]) > 40:
        out.append(f"- … {len(r['sentences']) - 40} more")

    e = r["eigen"]
    out.append(h("Eigen (a curiosity, beside the primary readings)"))
    out.append(f"- Yp = {e['yp']:.4f}; last key {e['last']:g}, next {e['next']:g} "
               f"({sfo.keys[e['next']].reading}) on {e['next_at']:%Y-%m-%d %H:%M}")

    out.append(h("Ahead in this SFO"))
    if r["ahead"]:
        for x, d in r["ahead"]:
            out.append(f"- {d:%Y-%m-%d %H:%M} · X = {x:g} — {sfo.keys[x].reading}")
    else:
        out.append("- no key of this SFO within the horizon")
    for x, d in r["eigen_ahead"]:
        joint = [k for k, dk in r["ahead"] if abs((dk - d).total_seconds()) < 60]
        tag = f" · jointly with X = {joint[0]:g} of this SFO" if joint else ""
        out.append(f"- {d:%Y-%m-%d %H:%M} · eigen crosses {x:g} — {sfo.keys[x].reading}{tag}")
    return "\n".join(out)
