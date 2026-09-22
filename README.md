# REVOTT

**Revelation Of The Trial.** One coordinate, and two additive shifts on it.

    TNLDY = 14160 + 100·Y + 100·X

    14160    REVOTT's own Ztp
    100·Y    the per-instance shift; Y names the instance
    100·X    the position, free to range up and down the SFO

    year  = TNLDY × 23/8400 + 1969 + 391/420
    date  = 1969-11-07T11:28:41.739Z + TNLDY days

Everything else — calendar dates, decimal years, the named readings — is a view of TNLDY.

The year unit is **8400/23 = 365.2174 days**, which is what the `48.3/17640` factor in the REVOTT
expression reduces to: `48.3/17640 = 23/8400`.

| TNLDY | date | what it is |
|---|---|---|
| 0 | 1969-11-07 | the TNLDY origin |
| **14160** | **2008-08-14** | **REVOTT's own Ztp**, Y = 0 |
| 16610 | 2015-04-30 | Y = 24.50 — a shift of 2450 |

## Usage

Two operations, matching how REVOTT is worked:

    python -m revott sweep --y 24.50                  # X across the whole SFO, dated
    python -m revott at --y 24.50 --x -147.6          # one position in one instance

and around them:

    python -m revott ztp                              # REVOTT's own zero
    python -m revott instance --y 82.80               # an instance's Ztp and span
    python -m revott sfo                              # the key structure and its anomalies
    python -m revott readings --x 0.00                # the eleven named readings
    python -m revott page --y 24.50                   # render an instance
    python -m revott sweep --y 24.50 --from -10 --to 10 --step 0.5 --csv

X is continuous. `sweep` with no range walks the 400 keys; with `--from/--to/--step` it walks
whatever you ask for, keyed or not.

## The SFO

X ranges over the SFO. The **400 BB keys** are a structure standing on it — positions carrying
framework text and naming successors — not a list X is confined to.

- **704 relations**: a **backbone** of 399, each key to the one immediately next, plus **305
  long-range** edges skipping over it. One root (−147.6), one sink (212.4), acyclic.
- **3 backbone links are not written down** in the source and hold by default: `−1.916 → −0.18`,
  `0.0 → 0.18`, `0.18 → 0.33`. Marked wherever they appear.
- **4 disputed gaps**, where the stated gap and the difference between the keys disagree. Both
  numbers are kept; neither is resolved.
- **15 keys carry no framework text.**
- **One erratum applied**: one source row carried two keys, `−0.18` and `0.18`. Separated, every
  gap reconciles, and the only backward edge and only ordering violation both resolve.

## The named readings

The corpus carries **eleven** named readings over the same positions at four scales — 3500D,
2800D/23, 100D, yG — held in `data/readings.json` and reachable with `revott readings`. They are
other views of the same domain.

## What is not here

No evidence, no correspondence, no selection. In particular there is no set of 265 positions: that
number is an artifact of an earlier matching process, not a property of the SFO, and nothing in
this package is conditioned on whether anything was once found near a position.

## Layout

    revott/core.py       the coordinate system; exact arithmetic throughout
    revott/sfo.py        the 400 keys, their text, their relations
    revott/readings.py   the eleven named readings
    revott/page.py       render an instance
    revott/cli.py        every command
    data/keys.json       the key structure, extracted once
    data/readings.json   the readings, 11 × 265 positions
    web/                 rendered instances
