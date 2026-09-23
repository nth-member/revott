#!/usr/bin/env python3
"""Rebuild the corpus manifests from GDELT's index page.

    python3 manifest.py CORPUS_DIR [--check]

GDELT used to publish `filesizes.txt` and `md5sums.txt` beside the archives, and
the corpus was first pulled against them. Both now 404 -- the site 301-redirects
to an https host that does not serve them -- so anything reading those files
alone will believe the corpus is complete forever and never see a new day.

`index.html` is still served and carries more than they did: for every archive a
name, a human-readable size, and an MD5.

    <LI><A HREF="20260921.export.CSV.zip">20260921.export.CSV.zip</A>
        (6.2MB) (MD5: 9e96d4e07ba98cce4287b243fbed14c3)

So md5sums.txt is regenerated from it exactly. filesizes.txt needs byte counts,
which the index only rounds, so existing entries are kept as they are and each
new archive gets one HEAD request for its Content-Length. That keeps both files
in the formats fetch.py and verify.py already read, and keeps them growing.

Refuses to write a manifest smaller than the one it would replace: a short parse
means a truncated download, and adopting it would erase the record of what the
corpus holds.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

INDEX = "http://data.gdeltproject.org/events/index.html"
BASE = "http://data.gdeltproject.org/events/"
ROW = re.compile(
    r'HREF="(?P<name>[^"]+\.zip)"[^>]*>(?P=name)</A>\s*'
    r'\([^)]*\)\s*\(MD5:\s*(?P<md5>[0-9a-f]{32})\)',
    re.I,
)


def curl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["curl", "-fLsS", "--retry", "3", "--retry-delay", "2",
         "--connect-timeout", "20", *args],
        capture_output=True, text=True,
    )


def fetch_index() -> list[tuple[str, str]]:
    r = curl("--max-time", "180", INDEX)
    if r.returncode != 0:
        sys.exit(f"index fetch failed: {r.stderr.strip()[:200]}")
    rows = [(m.group("name"), m.group("md5").lower()) for m in ROW.finditer(r.stdout)]
    if not rows:
        sys.exit("index fetched but no archive rows parsed — the page format changed")
    seen, out = set(), []
    for name, md5 in rows:
        if name not in seen:
            seen.add(name)
            out.append((name, md5))
    return out


def content_length(name: str) -> int | None:
    r = curl("-I", "--max-time", "60", BASE + name)
    if r.returncode != 0:
        return None
    size = None
    for line in r.stdout.splitlines():           # last hop wins
        if line.lower().startswith("content-length:"):
            size = int(line.split(":", 1)[1].strip())
    return size


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip().splitlines()[2].strip())
    root = Path(sys.argv[1]).expanduser().resolve()
    check = "--check" in sys.argv
    files, fs, ms = root / "files", root / "filesizes.txt", root / "md5sums.txt"

    # Archives GDELT indexes but does not serve. Without this they are counted
    # as "new" every run, HEADed for a size that never comes, and handed to
    # fetch.py to 404 again -- failure lines on a run where nothing is wrong,
    # which teaches you to ignore failures that matter.
    absent_file = root / "known_absent.txt"
    known_absent = set()
    if absent_file.exists():
        known_absent = {l.strip() for l in absent_file.read_text().splitlines()
                        if l.strip() and not l.startswith("#")}

    published = fetch_index()
    have_md5 = len([l for l in ms.read_text().splitlines() if l.strip()]) if ms.exists() else 0
    # md5sums.txt is written with the known-absent pruned out, so the index will
    # legitimately carry that many more. Add them back before comparing, or the
    # guard silently loosens by one per known-absent entry.
    floor = have_md5 + len(known_absent)
    print(f"   index lists {len(published)} archives (local md5sums.txt has {have_md5}"
          + (f" + {len(known_absent)} pruned" if known_absent else "") + ")")
    if len(published) < floor:
        sys.exit(f"   REFUSED: parsed {len(published)} rows, fewer than the {floor} already "
                 f"held. That is a bad download, not a shrinking corpus. Nothing written.")

    on_disk = {p.name for p in files.glob("*.zip")}
    missing = [n for n, _ in published if n not in on_disk and n not in known_absent]
    skipped = [n for n, _ in published if n not in on_disk and n in known_absent]
    print(f"   on disk {len(on_disk)}; genuinely absent {len(missing)}"
          + (f"; known-absent, not attempted {len(skipped)}" if skipped else ""))
    for n in missing[:5]:
        print(f"     {n}")
    if len(missing) > 5:
        print(f"     … and {len(missing) - 5} more")

    if check:
        return 0

    sizes: dict[str, int] = {}
    for line in fs.read_text().splitlines() if fs.exists() else []:
        p = line.split()
        if len(p) == 2 and p[0].isdigit():
            sizes[p[1]] = int(p[0])

    # Prune the known-absent from filesizes.txt too, every run. manifest.py can
    # skip them, but fetch.py reads filesizes.txt and will keep attempting -- and
    # failing -- anything listed there.
    pruned = [n for n in sizes if n in known_absent]
    for n in pruned:
        del sizes[n]

    added = 0
    if missing:
        print(f"   asking the server for the size of {len(missing)} new archives")
        for n in missing:
            s = content_length(n)
            if s:
                sizes[n] = s
                added += 1
            else:
                print(f"     no Content-Length for {n} — left out; fetch.py will skip it")

    # A recorded size the server has confirmed is kept over the index's claim.
    # GDELT's index can advertise a pre-republication size and MD5 long after the
    # server has moved on; §5b's rule is that the server decides, not the manifest.
    order = {n: i for i, (n, _) in enumerate(published)}
    fs.write_text("".join(
        f"{sizes[n]} {n}\n" for n in sorted(sizes, key=lambda x: order.get(x, 1 << 30))))
    ms.write_text("".join(f"{m}  {n}\n" for n, m in published if n not in known_absent))
    note = f", {len(pruned)} known-absent pruned" if pruned else ""
    print(f"   filesizes.txt: {len(sizes)} entries (+{added}{note});  "
          f"md5sums.txt: {len(published) - len(known_absent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
