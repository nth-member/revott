# REVOTT atop GDELT

**A position paper on the objective.** Written 2026-09-22, after the corpus was read and the
coordinate was stated correctly.

---

## 1. The objective

**Not to find events. To obtain a denominator.**

Asked of any date since 1974, *did something happen?* returns yes. The answer carries no
information because the question has no negative branch. Evidence gathered that way cannot fail,
and evidence that cannot fail is not evidence.

GDELT supplies a continuous daily series, so the question becomes *what is the state of the field
at this position, and how is it changing?* That question has a negative branch. It is the whole
reason for the corpus.

The objective, stated once: **to put REVOTT in a position to come back negative, and to see whether
it does.**

---

## 2. REVOTT is one coordinate and one sum

```
TNLDY(Y, X) = 14160 + 100·(Y + X)

date(TNLDY)  = 1969-11-07T11:28:41.739Z + TNLDY days
year(TNLDY)  = TNLDY × 23/8400 + 1969 + 391/420
```

`14160` is REVOTT's own Ztp. `48.3/17640` reduces exactly to `23/8400`, so one year is `8400/23 =
365.2173913` days; `5849 + 391/420 − 3880` reduces exactly to `1969 + 391/420`.

**Y and X enter identically.** The expression contains only their sum. Three consequences, and they
are not observations about the implementation but properties of the coordinate:

- **Y and X have the same span**, `−147.60 .. 212.40`, 360 units = 36,000 days each.
- `Y + X` runs `−295.20 .. 424.80`, TNLDY `−15,360 .. 56,640`, dates **1927-10-19 .. 2124-12-04**.
- **Sliding the anchor is a shift test.** Position X in the instance shifted by Y falls on the same
  date as X′ in Y′ whenever `Y + X = Y′ + X′`. A sweep over Y therefore generates its own null; no
  separate construction is needed, and none should be built.

An instance is a *shift*, not an object with its own epoch. Y names the instance; X is the position.

---

## 3. The SFO units

**This is the point most easily got wrong, and getting it wrong invalidates everything downstream.**

**The units of X are the 400 SFO-BB node values.** X is not stepped in ones, and one unit of X is
not a meaningful quantum of the work. The nodes are irregular:

```
400 nodes, −147.60 .. 212.40
263 distinct gaps
tightest gap      0.09 days
most common gap  10.80 days   (×33)
also common     252.00 days   (×11),  20.00 (×10),  1.97 (×7),  18.00 (×7),  10.00 (×7)
228 of the 399 consecutive pairs sit closer than 18 days apart
```

Three things follow immediately:

1. **No argument may rest on a fixed step in X.** Any reasoning of the form "one unit of X is 100
   days, therefore …" is about a grid that does not exist.
2. **Nodes can be arbitrarily close, and can coincide.** At Y = 24.50, the 366 nodes that land
   inside GDELT's range fall on 358 distinct dates; eight pairs share a date outright. A count of
   nodes is not a count of independent observations, and must never be reported as one.
3. **Tight clusters see correlated field values.** Nodes 0.09 days apart read the same day. Nodes a
   few days apart read a field that is autocorrelated over weeks.

Y is the same coordinate and so carries the same span, but Y is swept at **day resolution** —
`0.01` of Y is exactly one day — because Y is a shift, not a position on the SFO. That asymmetry in
how the two are *used* is the only asymmetry between them.

---

## 4. The SFO is a DAG, which is what makes the readout a path

```
400 nodes, 704 successor edges (701 stated, 3 implied to close the backbone)
every edge runs forward in X;  gap = target − source, in X units (×100 = days)

  backbone     399    node -> the very next node
  long-range   305    node -> a node further on

  one root  −147.60   nothing points at it
  one sink   212.40   it names nothing
```

Fan-out: 214 nodes name one successor, 123 name two, 32 three, 20 four, 8 five, one names 9, one
names 19. Fan-in: 179 have one predecessor, 160 two, 44 three, 9 four, 6 five, one has 7.

**The backbone is exactly consecutive-in-x**, so it orders the readout the way the calendar already
does. It adds nothing a date-sorted list does not have. **The content of the DAG is its 305
long-range edges** — the relations that skip ahead, whose gaps cluster at 360 days (×23), 181
(×14), 179 (×14), 252 (×13), 10.8 (×11), 483 (×8).

This is why the objective is stated against a *path* and not a set of hits. A set has no order and
no relations; a path ordered by the backbone and cross-braced by 305 long-range edges has both, and
both are testable properties that an arbitrary path through the same field need not have.

---

## 5. GDELT is the denominator, and it is not a clean one

```
1979-01-01 .. 2026-09-20     17,430 days     17,406 present     24 NULL
```

Five properties of the corpus, each of which is a correctness issue rather than a caveat:

**Two eras, and they measure different quantities.** Before 2013-04-01 the archives are yearly and
monthly, partitioned by the date an event is attributed to. From 2013-04-01 there is one archive
per ingestion day. Both are defensible daily series; they are not the same series, and anything
spanning the seam compares across it.

**24 NULL days, never zero.** GDELT never published 22 of them — including a contiguous 18-day
outage, 2025-06-14 to 2025-07-01 — and 2 more are listed in its manifest but absent from its
server. Read as zero, each would be the largest single-day collapse in fifty years. Because the
nodes are tightly spaced (§3), an anchoring can place several inside one gap.

**Non-stationary by two orders of magnitude.** ~1,200 events/day in 1979, ~220,000 in 2016, with
collection step changes at 1996, 2006, 2013-04 and 2015-02 that belong to GDELT's history and not
the world's.

**A weekly cycle worth 70% of the residual.** Saturday and Sunday run at 0.57–0.69× a Wednesday,
and the ratio drifts across decades.

**An annual cycle worth 47% of the residual.** Jan 1 averages far below trend and Dec 25 close
behind, every year. A centred rolling median straddles the holiday fortnight with eleven normal
weeks and leaves it almost intact.

Both cycles alias a sweep over Y, because one Y step is one day and so rotates the whole path's
weekday and day-of-year together. **Therefore: nothing raw.** Every reading is taken against a
local baseline in log space, with the weekday and the day-of-year removed locally and the NULLs
propagated as NULL.

---

## 6. What the composition is

```
REVOTT :  (Y, X)  ->  date
GDELT  :  date    ->  a number

Hold Y.  Run X over the 400 node values.  Read the field at each.
```

That is the entire instrument. Everything else is the discipline required to read it honestly.

---

## 7. What may be concluded, and what may not

**Coverage bounds the question before any statistic does.** The path spans 36,000 days — 98.6 years
— and GDELT spans 47.7. **No value of Y places all 400 nodes inside the field.** Every reading is
partial, the partial fraction varies with Y, and counts are therefore not comparable across
anchorings. Rates are, and only among anchorings covering enough nodes for a rate to mean anything.

**There are no p-values in this work.** A reading is a *percentile against the field's own
distribution*; an anchoring is a *rank against the sweep*. Never a sigma, never a significance
claim. The honest headline is "this anchoring ranks Nth of M", and if the rank is unremarkable,
that is the finding.

**The statistic is fixed before the sweep, not after seeing one.** Y at day resolution over the
full span is tens of thousands of anchorings; take the best of them and something extraordinary
appears from noise with certainty. Any statistic must be declared, and checked for aliasing against
the weekly and annual cycles, before it is run.

**A rank must survive inspection.** A feature that vanishes under a one-day shift in Y is not a
feature — the field is autocorrelated, and a real one would not. A rank that rests on a handful of
nodes crossing a threshold is measuring the discreteness of a count. Adjacent anchorings are
strongly correlated, so the number of effectively independent draws is far below the number swept,
and the rank must be read against that.

**The instrument must be able to return negative.** This is the governing constraint, not a
concession. *The more you look the less you see*: research every position and the hit rate
converges on the base rate, and each finding means less. The work is sized to produce a comparison,
not a list, and a negative reading is a result that the design is obliged to be capable of
producing.

---

## 8. Scope

Everything above traverses the 100D scale on the raw position. It is one traversal of the
coordinate, and a reading obtained through it — positive or negative — is a reading about that
traversal. It should never be written as though it were a reading about the structure.
