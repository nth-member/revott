"""The author's edges: the edges the author gives that the SFO-WAM omits, kept in one record and carried
everywhere the SFO's edges are carried (E-005).

    revott edge add FROM TO [FROM TO ...] [--said TEXT]   record the edges and carry them everywhere
    revott edge remove FROM TO [FROM TO ...]              take recorded edges out again, everywhere
    revott edge list                                      the record
    revott edge check                                     every value and every carrier, without writing
    revott edge sync                                      carry the whole record again (idempotent)

The author's rule (2026-11-22): every place the SFO-WAM indicates an edge is an edge, and a wrong value found
there is human error. So an edge's value is always the difference between its keys. It is computed here, never
typed in. FROM and TO must already be keys, and FROM must come before TO, since the SFO runs forward in time.

Carried to:
- REVOTT: data/keys.json, docs/data/nodes.json, the out-degree column of gdelt/overlay_Y24p5.csv and the counts
  in README.md;
- the member (~/member): docs/data/sfo.json and the edge counts in README.md, docs/index.html and build.py;
- JOMO SFO-WAM (~/jomo-sfo-wam): EDGES_RAW in src/sfo_wam_engine.jsx, its counts, README.md, and the built docs/;
- the research copies ~/Projects/jomo-sfo-wam*/src/sfo_wam_engine.jsx (source only; each is backed up once
  under ~/Projects/backup-before-author-edges/).

In JOMO, a value that disagrees with the corrected REVOTT value on the same stated edge is aligned to it.
Nothing is committed or pushed.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / "data" / "keys.json"
RECORD = ROOT / "data" / "author_edges.json"
OVERLAY = ROOT / "gdelt" / "overlay_Y24p5.csv"
README = ROOT / "README.md"
HOME = Path.home()
MEMBER = Path(os.environ.get("MEMBER", HOME / "member"))
JOMO = Path(os.environ.get("JOMO", HOME / "jomo-sfo-wam"))
COPIES = HOME / "Projects"
BACKUP = COPIES / "backup-before-author-edges"
TOL = Decimal("0.005")
NSUKKA = timezone(timedelta(hours=1))

NOTE = ("Edges the author gives that the SFO-WAM omits (E-005). Every place the SFO-WAM indicates an edge is an "
        "edge, and a wrong value found there is human error, so each value is the difference between its keys. "
        "Add with: python3 -m revott edge add FROM TO --said \"the author's words\"")


# ---- keys.json, exactly as written -------------------------------------------------------------------------

def _ser(o) -> str:
    if isinstance(o, dict): return "{" + ",".join(json.dumps(k) + ":" + _ser(v) for k, v in o.items()) + "}"
    if isinstance(o, list): return "[" + ",".join(_ser(v) for v in o) + "]"
    if isinstance(o, Decimal): return str(o)
    if isinstance(o, bool): return "true" if o else "false"
    if o is None: return "null"
    if isinstance(o, int): return str(o)
    return json.dumps(o)


def _read_keys() -> dict:
    raw = KEYS.read_text(encoding="utf-8")
    K = json.loads(raw, parse_float=Decimal)
    assert _ser(K) == raw, "keys.json does not round-trip"
    return K


def _diff(a: Decimal, b: Decimal) -> Decimal:
    return Decimal(format((b - a).normalize(), "f"))


def _counts(K: dict) -> tuple[int, int, int, int]:
    """keys, relations, backbone, long-range"""
    n_rel = sum(len(k["successors"]) for k in K["keys"]) + len(K["implied_backbone"])
    n_bb = len(K["keys"]) - 1
    return len(K["keys"]), n_rel, n_bb, n_rel - n_bb


# ---- the record ------------------------------------------------------------------------------------------

def _record() -> dict:
    if RECORD.exists():
        return json.loads(RECORD.read_text(encoding="utf-8"))
    return {"note": NOTE, "edges": []}


def _write_record(R: dict) -> None:
    RECORD.write_text(json.dumps(R, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _validate(K: dict, a: str, b: str) -> str | None:
    xs = {k["x"] for k in K["keys"]}
    da, db = Decimal(a), Decimal(b)
    if da not in xs: return f"{a} is not a key (give the key first)"
    if db not in xs: return f"{b} is not a key (give the key first)"
    if not da < db: return f"{a} -> {b} runs backward; the SFO runs forward in time"
    return None


# ---- carrying ------------------------------------------------------------------------------------------------

def _carry_keys(K: dict, R: dict) -> list[str]:
    byx = {k["x"]: k for k in K["keys"]}
    done = []
    for e in R["edges"]:
        a, b = Decimal(e["from"]), Decimal(e["to"])
        src = byx[a]
        if b not in [t for t, _ in src["successors"]]:
            src["successors"].append([b, _diff(a, b)])
            src["successors"].sort(key=lambda s: s[0])
            done.append(f"{e['from']} -> {e['to']} ({_diff(a, b)})")
    return done


def _carry_overlay(K: dict) -> list[str]:
    """Rewrite only the out-degree cells that changed; every other byte of the overlay stays as it is."""
    if not OVERLAY.exists():
        return []
    s = OVERLAY.read_text(encoding="utf-8", newline="")
    rows = list(csv.DictReader(io.StringIO(s, newline="")))
    deg = {float(k["x"]): len(k["successors"]) for k in K["keys"]}
    nl = "\r\n" if "\r\n" in s else "\n"
    lines = s.split(nl)
    changed = []
    for r in rows:
        new = deg.get(float(r["x"]))
        if new is None or str(new) == r["out_degree"]:
            continue
        hits = [i for i, l in enumerate(lines) if l.startswith(r["x"] + ",")
                and l.split(",", 12)[10] == r["out_degree"]]
        assert len(hits) == 1, f"overlay row {r['x']} not found exactly once"
        f = lines[hits[0]].split(",", 12)
        f[10] = str(new)
        lines[hits[0]] = ",".join(f)
        changed.append(f"{r['x']} {r['out_degree']}->{new}")
    if changed:
        OVERLAY.write_text(nl.join(lines), encoding="utf-8", newline="")
    return changed


def _carry_readme(K: dict) -> bool:
    n_keys, n_rel, n_bb, n_lr = _counts(K)
    s = README.read_text(encoding="utf-8")
    pat = (r"- \*\*\d+ relations\*\*: a \*\*backbone\*\* of \d+, each key to the one immediately next, plus \*\*\d+"
           r"\n  long-range\*\*")
    new = (f"- **{n_rel} relations**: a **backbone** of {n_bb}, each key to the one immediately next, plus **{n_lr}"
           f"\n  long-range**")
    assert re.search(pat, s), "README relation count not found"
    s2 = re.sub(pat, new, s, count=1)
    if s2 != s:
        README.write_text(s2, encoding="utf-8")
    return s2 != s


def _carry_member(K: dict) -> list[str]:
    if not (MEMBER / "build.py").exists():
        return [f"member: {MEMBER} not found, skipped"]
    n_keys, n_rel, _, _ = _counts(K)
    snippet = (
        "import build\n"
        "from build import SFO\n"
        "sfo = SFO()\n"
        "nodes = [{'x': x, 'r': k.reading, 'm': k.marks, 'a': k.apoc, 'd': k.derived,\n"
        "          'c': k.primary_from if not k.has_primary else None}\n"
        "         for x, k in ((x, sfo.keys[x]) for x in sfo.order)]\n"
        "edges = [[e.source, e.target, 1 if e.default else 0] for e in sfo.edges]\n"
        "build.dump('sfo.json', {'nodes': nodes, 'edges': edges})\n")
    subprocess.run([sys.executable, "-c", snippet], cwd=MEMBER, check=True, stdout=subprocess.DEVNULL,
                   env={**os.environ, "REVOTT": str(ROOT)})
    out = ["member: docs/data/sfo.json"]
    for name, pat, rep in (
            ("README.md", r"\d+-node, \d+-edge SFO", f"{n_keys}-node, {n_rel}-edge SFO"),
            ("docs/index.html", r"\d+-node, \d+-edge SFO", f"{n_keys}-node, {n_rel}-edge SFO"),
            ("build.py", r"REVOTT's \d+ keys read in layers, and its \d+ edges",
             f"REVOTT's {n_keys} keys read in layers, and its {n_rel} edges")):
        p = MEMBER / name
        s = p.read_text(encoding="utf-8")
        s2 = re.sub(pat, rep, s)
        if s2 != s:
            p.write_text(s2, encoding="utf-8")
            out.append(f"member: {name}")
    return out


def _jomo_patch(path: Path, author: list[tuple[Decimal, Decimal]], stated: dict,
                drop: list[tuple[Decimal, Decimal]] = ()) -> dict:
    """Add the author's edges to a JOMO engine source and align any value that disagrees with REVOTT's corrected
    value on the same stated edge. JOMO keeps its own node list (it never split -0.18/0.18); an edge whose ends it
    lacks is reported, not invented."""
    s = path.read_text(encoding="utf-8")
    m = re.search(r"const NODE_YS=\[([^\]]*)\];", s)
    me = re.search(r"const EDGES_RAW=(\[\[[\s\S]*?\]\]);", s)
    if not (m and me):
        return {"path": str(path), "error": "NODE_YS / EDGES_RAW not found"}
    ys = [Decimal(v.strip()) for v in m.group(1).split(",") if v.strip()]
    ix = {float(y): i for i, y in enumerate(ys)}          # by number: JOMO writes values as floats
    E = json.loads(me.group(1))
    removed = []
    for a, b in drop:
        if float(a) in ix and float(b) in ix and (float(a), float(b)) not in stated:
            keep = [row for row in E if not (row[0] == ix[float(a)] and row[1] == ix[float(b)])]
            if len(keep) != len(E):
                E = keep; removed.append(f"{a} -> {b}")
    at = {(a, b): n for n, (a, b, _) in enumerate(E)}
    added, aligned, lacking = [], [], []
    for a, b in author:
        i, j = ix.get(float(a)), ix.get(float(b))
        if i is None or j is None:
            lacking.append(f"{a} -> {b}"); continue
        if (i, j) not in at:
            E.append([i, j, float(_diff(a, b))]); at[(i, j)] = len(E) - 1
            added.append(f"{a} -> {b}")
    for (fa, fb), (a, b, v) in stated.items():
        i, j = ix.get(fa), ix.get(fb)
        if i is not None and j is not None and (i, j) in at:
            row = E[at[(i, j)]]
            if abs(Decimal(str(row[2])) - v) > Decimal("1e-9") and v == _diff(a, b):
                aligned.append(f"{a} -> {b} {row[2]}->{v}")
                row[2] = float(v)
    E.sort()
    if added or aligned or removed:
        name = path.parent.parent.name
        if path.parent.parent != JOMO:
            keep = BACKUP / name / path.name
            if not keep.exists():
                keep.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, keep)
        s = s[:me.start()] + "const EDGES_RAW=" + json.dumps(E, separators=(",", ":")) + ";" + s[me.end():]
        s = re.sub(r"// \d+ nodes · \d+ edges · Four Operations", f"// {len(ys)} nodes · {len(E)} edges · Four Operations",
                   s, count=1)
        s = re.sub(r"// ── \d+ EDGES \[fromIdx, toIdx, weight\] ──", f"// ── {len(E)} EDGES [fromIdx, toIdx, weight] ──",
                   s, count=1)
        path.write_text(s, encoding="utf-8")
    return {"path": str(path), "nodes": len(ys), "edges": len(E), "added": added, "aligned": aligned,
            "removed": removed, "lacking": lacking}


def _carry_jomo(K: dict, R: dict, build: bool = True, drop=()) -> list[str]:
    author = [(Decimal(e["from"]), Decimal(e["to"])) for e in R["edges"]]
    stated = {(float(k["x"]), float(t)): (k["x"], t, g) for k in K["keys"] for t, g in k["successors"]}
    out = []
    srcs = [JOMO / "src" / "sfo_wam_engine.jsx"] + sorted(
        p for p in COPIES.glob("jomo-sfo-wam*/src/sfo_wam_engine.jsx") if "_backup_" not in str(p))
    live_changed = False
    for p in srcs:
        if not p.exists():
            continue
        r = _jomo_patch(p, author, stated, drop)
        if r.get("error"):
            out.append(f"JOMO {p}: {r['error']}"); continue
        tag = "JOMO" if p.parent.parent == JOMO else f"copy {p.parent.parent.name}"
        if r["added"] or r["aligned"] or r["removed"]:
            out.append(f"{tag}: {r['nodes']} nodes, {r['edges']} edges; added {r['added']}; aligned {r['aligned']}"
                       + (f"; removed {r['removed']}" if r['removed'] else ""))
            live_changed |= p.parent.parent == JOMO
        if r["lacking"]:
            out.append(f"{tag}: lacks the ends of {r['lacking']}")
        if p.parent.parent == JOMO:
            rd = JOMO / "README.md"
            s = rd.read_text(encoding="utf-8")
            s2 = re.sub(r"\(\d+ nodes, \d+ edges\)", f"({r['nodes']} nodes, {r['edges']} edges)", s, count=1)
            if s2 != s:
                rd.write_text(s2, encoding="utf-8"); out.append("JOMO: README.md")
    if live_changed and build:
        if (JOMO / "node_modules").exists():
            subprocess.run(["npm", "run", "build"], cwd=JOMO, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            out.append("JOMO: docs/ rebuilt (npm run build)")
        else:
            out.append("JOMO: node_modules missing; run `npm ci && npm run build` in ~/jomo-sfo-wam")
    return out


def sync(build: bool = True, drop=()) -> list[str]:
    K, R = _read_keys(), _record()
    for e in R["edges"]:
        err = _validate(K, e["from"], e["to"])
        assert not err, err
    out = [f"REVOTT: {s}" for s in _carry_keys(K, R)]
    KEYS.write_text(_ser(K), encoding="utf-8")
    subprocess.run([sys.executable, "docs/build_data.py"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    out += [f"REVOTT overlay out-degree: {c}" for c in _carry_overlay(K)]
    if _carry_readme(K):
        out.append("REVOTT: README counts")
    out += _carry_member(K)
    out += _carry_jomo(K, R, build=build, drop=drop)
    n_keys, n_rel, n_bb, n_lr = _counts(K)
    out.append(f"SFO: {n_keys} keys, {n_rel} relations ({n_bb} backbone, {n_lr} long-range); "
               f"{len(R['edges'])} edges in the author's record")
    return out


def add(pairs: list[str], said: str | None, defer: bool = False, build: bool = True) -> int:
    if len(pairs) % 2:
        print("give the edges as pairs: FROM TO [FROM TO ...]"); return 2
    K, R = _read_keys(), _record()
    have = {(e["from"], e["to"]) for e in R["edges"]}
    stated = {(k["x"], t) for k in K["keys"] for t, _ in k["successors"]} | \
             {(d["from"], d["to"]) for d in K["implied_backbone"]}
    today = datetime.now(NSUKKA).date().isoformat()
    new = []
    for a, b in zip(pairs[::2], pairs[1::2]):
        err = _validate(K, a, b)
        if err:
            print(f"refused: {err}"); return 1
        if (a, b) in have:
            print(f"already in the record: {a} -> {b}"); continue
        if (Decimal(a), Decimal(b)) in stated:
            print(f"already an edge of the SFO: {a} -> {b}"); continue
        v = _diff(Decimal(a), Decimal(b))
        e = {"from": a, "to": b, "value": str(v), "given": today}
        if said:
            e["said"] = said
        R["edges"].append(e); new.append(f"{a} -> {b} ({v})")
    if not new:
        return 0
    _write_record(R)
    print("recorded: " + "; ".join(new))
    if defer:
        print("deferred: run `python3 -m revott edge sync` to carry them"); return 0
    for line in sync(build=build):
        print("  " + line)
    return 0


def remove(pairs: list[str], build: bool = True) -> int:
    """Only edges in the author's record can be removed here; the SFO-WAM's own edges stand."""
    if len(pairs) % 2 or not pairs:
        print("give the edges as pairs: FROM TO [FROM TO ...]"); return 2
    K, R = _read_keys(), _record()
    gone = []
    for a, b in zip(pairs[::2], pairs[1::2]):
        hit = [e for e in R["edges"] if Decimal(e["from"]) == Decimal(a) and Decimal(e["to"]) == Decimal(b)]
        if not hit:
            print(f"not in the author's record: {a} -> {b}; the SFO-WAM's own edges are not removed here"); return 1
        R["edges"].remove(hit[0]); gone.append((Decimal(a), Decimal(b)))
    byx = {k["x"]: k for k in K["keys"]}
    for a, b in gone:
        byx[a]["successors"] = [s for s in byx[a]["successors"] if s[0] != b]
    KEYS.write_text(_ser(K), encoding="utf-8"); _write_record(R)
    print("removed: " + "; ".join(f"{a} -> {b}" for a, b in gone))
    for line in sync(build=build, drop=gone):
        print("  " + line)
    return 0


def check() -> int:
    K, R = _read_keys(), _record()
    bad = 0
    wrong = [(k["x"], t, g) for k in K["keys"] for t, g in k["successors"] if abs((t - k["x"]) - g) > TOL]
    for a, b, g in wrong:
        print(f"value is not the difference: {a} -> {b} stated {g}, keys give {_diff(a, b)}"); bad += 1
    byx = {k["x"]: k for k in K["keys"]}
    sfo_json = MEMBER / "docs" / "data" / "sfo.json"
    member_edges = ({(float(a), float(b)) for a, b, _ in json.loads(sfo_json.read_text())["edges"]}
                    if sfo_json.exists() else None)
    jsx = JOMO / "src" / "sfo_wam_engine.jsx"
    jomo = None
    if jsx.exists():
        s = jsx.read_text(encoding="utf-8")
        ys = [Decimal(v.strip()) for v in re.search(r"const NODE_YS=\[([^\]]*)\];", s).group(1).split(",") if v.strip()]
        jomo = {(float(ys[a]), float(ys[b])) for a, b, _ in json.loads(re.search(r"const EDGES_RAW=(\[\[[\s\S]*?\]\]);", s).group(1))}
    for e in R["edges"]:
        a, b = Decimal(e["from"]), Decimal(e["to"])
        where = []
        if b not in [t for t, _ in byx[a]["successors"]]: where.append("REVOTT")
        if member_edges is not None and (float(a), float(b)) not in member_edges: where.append("member")
        if jomo is not None and (float(a), float(b)) not in jomo: where.append("JOMO")
        if where:
            print(f"not yet carried: {e['from']} -> {e['to']} missing in {', '.join(where)}"); bad += 1
    n_keys, n_rel, n_bb, n_lr = _counts(K)
    print(f"{n_keys} keys, {n_rel} relations ({n_bb} backbone, {n_lr} long-range); "
          f"{len(R['edges'])} author edges; {'all consistent' if not bad else f'{bad} to fix'}")
    return 1 if bad else 0


def listing() -> int:
    R = _record()
    if not R["edges"]:
        print("no author edges recorded"); return 0
    for e in R["edges"]:
        print(f"{e['from']:>10} -> {e['to']:<10} {e['value']:>8}   given {e['given']}"
              + (f"   \"{e['said']}\"" if e.get("said") else ""))
    return 0
