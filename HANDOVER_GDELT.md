# Handover — GDELT for REVOTT

Written 2026-09-22. What the corpus is, why it is here, what must not be done naively with it, and
where it sits in relation to the repositories.

---

## 1. The formula

The REVOTT expression, as written:

    (((((100)×((Y)+(0)))+(100×((X)+(0÷35)))+(((14160))+(0÷7)))×(48.3÷17640))+5849+(391÷420)−3880)

Term by term:

| term | is |
|---|---|
| `100×(Y+0)` | the per-instance shift. **Y names the instance.** |
| `100×(X+0÷35)` | the position. **X is free to range up and down the SFO.** |
| `14160+0÷7` | **REVOTT's own Ztp**, in TNLDY |
| `×(48.3÷17640)` | TNLDY → years |
| `+5849+(391÷420)−3880` | the year offset |

`0÷35` and `0÷7` both vanish; they are placeholders in the written form, and the parameters are
Y and X alone.

**Reductions, all exact:**

    48.3 ÷ 17640        = 23/8400          (so one year = 8400/23 = 365.2173913 days)
    5849 + 391/420 − 3880 = 1969 + 391/420 = 1969.9309523809525

**So the expression is two statements:**

    TNLDY(Y, X) = 14160 + 100·Y + 100·X
    year(TNLDY) = TNLDY × 23/8400 + 1969 + 391/420

and, since the corpus carries TNLDY on every node, a third follows from it:

    date(TNLDY)  = 1969-11-07T11:28:41.739Z + TNLDY days

**Verified against the corpus:** at Y = 24.50, `TNLDY = 16610 + 100X` holds for every position with
**zero deviation**, and the dates it yields reproduce the corpus exactly.

| Y | X | TNLDY | year | date |
|---|---|---|---|---|
| 0 | 0 | 14160 | 2008.702381 | 2008-08-14 |
| 24.50 | 0 | 16610 | 2015.410714 | 2015-04-30 |
| 24.50 | −147.6 | 1850 | 1974.996429 | 1974-12-01 |
| 34.918 | 0 | 88259/5 | 2018.263262 | 2018-03-07 |
| 82.80 | 0 | 22440 | 2031.373810 | 2031-04-16 |
| 85.32 | 0 | 22692 | 2032.063810 | 2031-12-24 |

Inverses, in `revott/core.py`: `tnldy_at_date`, `x_at_date(when, y)`, `y_for_ztp(year)`.

**The corpus states the inverse itself.** `~/sfo_mdqnm_agent_build/CANONICAL READOUT — EQUATION OF
THE SHIFTING ZEROES.xlsx` carries, in its header:

    −(17640/48.3)·Y + 48261.3 = Z    (TNLDY)
     (14.49/17640)·Z + 2419.979286 = Z′  (YGADi)
     Z′ + (3/10)·U = V    (YGADi),  −630 ≤ U ≤ 0

with a domain line reading `…8568/8532…8480/8360/8280 ≥ Y ≥ 0` — the shifting zeroes in day units,
i.e. 85.68, 85.32, 84.80, 83.60, 82.80 × 100. **That workbook has not been read properly yet**, and
it is the most direct source for the family of instances and the YGADi reading.

## 2. The nuances that govern this work

These are the corpus author's own statements about their system, recorded because each of them
overturned something already built. None is derivable from the files. A reader who has only the
arithmetic will re-make these mistakes, as this session did, repeatedly.

**REVOTT is the Revelation Of The Trial.** The name is not decorative and the system is not the
whizz-kids story; that story is one reading of one instance.

**Y is the instance shift; X ranges freely.** "The REVOTT Ztp is 14160.0 TNLDY … the fixed Y (e.g.
24.50) contributes to the per-instance Ztp shift (thus 14160 + 2450) … while the X is free to range
up and down the SFO." So an instance is a *shift*, not a separate object with its own epoch.
Modelling each anchoring as an independent instance file with its own epoch — which this repo did
at first — is wrong, and makes four values of one parameter look like four systems.

**The two operating modes.** "I typically hold a given Y fixed (like 24.50) and run all Xs against
it, OR investigate a given X (or a few given Xs) against it." The first is the sweep. The second is
the pre-registered test — naming positions before looking. Any scan design that does not reduce to
one of these is not how REVOTT is worked.

**Instances are siblings, never descendants.** "again_born is not a child of whizz_kids … it is an
independent slice of REVOTT." Each is anchored by its own Ztp. Relations between them — the exact
5830, 6082, 252-day separations — are *relations*, recorded as such, and never derivations. In
particular whizz-kids is not the reference frame; it is simply the slice that had reachable
real-world targets.

**There is no such thing as 265.** "265 is a number that came about because the 'Wired etc'
matches … this specific implementation was constrained to 265 because of a mandate to hit
real-world server targets — but it still has 400." The 265 is a **result set**, not a structure.
Positions were retained *because* a match was found, and then evidenced by the same criterion that
retained them. A hit rate over that set is near 1 because of how it was built, not because the
dates are special. Nothing may be conditioned on it.

**Latent context travels; server hits do not.** "The latent context should remain … etc Carnegie
stages … just not any server hits." The framework the SFO carries — somite counts and
Carnegie-stage markers, follicular phases, hidden-counts and year notations — belongs to the
domain and appears under any anchoring. Evidence, sources, correspondences and design-story
chapters belong to the instance that was sampled against the record, and do not travel. Rendering a
re-anchored instance stripped of its framework, as this repo did at first, is also wrong.

**No more Wired.** Withdraw any policy that prefers the sources the ledger already cites. The
reason is in §3, and it generalises: a criterion that selected the data must not also be the
criterion that evidences it.

**"It's about connecting the dots … because the more you look the less you see."** This is the
governing methodological constraint and the reason the control exists. Exhaustive coverage is not
merely expensive, it is self-defeating: research every position and the hit rate converges on the
base rate, and each individual finding means less. The instrument must be able to come back
negative, and the work must be sized to produce a comparison rather than a list. A cost table that
optimises for coverage — as this session first produced — has the epistemics backwards.

**The fluid-mechanics frame.** "Think velocity potential and stream function of fluid mechanics."
An instance is one slice of a larger analytic object, the way a streamline is one level set of a
complex potential. φ and ψ are each defined only up to a constant; fixing the constant selects the
particular flow. The REVOTT expression is that gauge-fixing, and the eleven named readings —
KINGS.3500D, NAPOLEON.3500D, 10DT_ARM.2800D/23, EXE_TPDP.100D, WITNESS_CFH_ENTER/LEAVE.100D,
TWG_TWF.100D, THE_DESTROYER.100D, ZTS_EON.yG, END_IE_PURPOSE_BIRTH/CIRCUMSPECTION.100D — are
conjugate views over the same domain at four scales. This implementation traverses one of them, the
100D scale on the raw position. It is a slice, and should never be written as though it were the
structure.

**What follows for GDELT.** The field is measured against a *path*, not a set of hits; the path is
ordered by the backbone; instances are siblings so every other Y is a legitimate control; the 265
never enters; and the statistic is fixed before the sweep because looking harder is how the signal
is destroyed.

## 3. Why GDELT

Not to find more events. To supply a **denominator**.

Web search answers *did something happen on this date?* — which is yes for any date since 1974, and
so carries no information. GDELT resolves to the day continuously from **1979-01-01** (though not
in daily *files* before 2013-04 — §4, §5c), so the question becomes *what is the state of the field at this position, and its derivative?* That is answerable,
and it can come back negative.

This replaced an earlier approach that had to be withdrawn. The SFO-BB ledger's most common form of
evidence was "a report was published that day", 95 of 96 same-day items drawn from one archive that
publishes every weekday — true of almost any date in its range. Naming those domains as preferred
sources would have trained a witness to reproduce exactly that. See the whizz-kids repo's commit
`003cb08`.

The framing that follows from it: the daily series is a **scalar field over time**; an instance's
positions are a **path** through it; the backbone orders that path. The backbone is exactly
consecutive-in-x, so it orders the path the way the calendar already does — what the DAG adds over
a date-sorted list is its **305 long-range edges**. See §7. The testable question is
whether that path has properties arbitrary paths through the same field do not — local extrema,
sign changes in the derivative, monotone segments between successor edges. Intervals become
gradients rather than pairs of hits.

---

## 4. What is on disk

    ~/gdelt_raw_1979_2026/
    ├── files/            5,012 zips · 53.7 GB · 1979-01-01 .. 2026-09-20
    ├── filesizes.txt     GDELT's published manifest, 5,014 entries
    ├── md5sums.txt       GDELT's published checksums
    ├── fetch.py          resumable, idempotent fetcher
    ├── verify.py         md5 first; the server decides when the manifest is stale
    ├── fetch.log         the run; fetch.log.1 is an earlier partial run
    └── (the aggregate lives in revott/gdelt/, not here)

Fetched in 1.14 h at ~11 MB/s. Verified: **5,011 md5-exact, 1 restated, 2 absent, 0 bad.**

**The 5,012 archives are not 5,012 days.** Three granularities, and the difference is not cosmetic
— see §5c:

    27  yearly    1979.zip .. 2005.zip               57 columns, keyed by event date
    87  monthly   200601.zip .. 201303.zip           57 columns, keyed by event date
  4897  daily     20130401 .. 20260920 .export.CSV   58 columns, keyed by ingestion day
     1  GDELT.MASTERREDUCEDV2.1979-2013.zip          a reduced restatement; not in the series

Columns 1–57 are identical across all three; the daily files add SOURCEURL as 58. Verified row by
row over the whole corpus: no day is covered twice, no SQLDATE falls outside its file's period, and
no row is malformed.

**Re-running `fetch.py` is safe at any time.** A file whose size matches is skipped, a partial is
continued, nothing is deleted. `verify.py` is read-only. **Nothing unzips the corpus** — the
aggregate streams each archive through `unzip -p` and the files stay compressed.

---

## 5. Four facts about this corpus that are correctness issues, not trivia

*(a) and (c) were corrected and (d) added on 2026-09-22, from the aggregate. Each was wrong or
absent in the version written before the files were read.)*

**(a) Twenty-four days are missing, and they must read as NULL, never zero.**

Corrected 2026-09-22 from the aggregate. The earlier figure of two counted only the files that
disagree with GDELT's manifest. The manifest itself skips 22 further days, so the *series* has 24
holes, in two kinds:

    never published by GDELT — absent from its own manifest (22 days)
      2014-01-23 .. 2014-01-25      3 days
      2014-03-19                    1 day
      2025-06-14 .. 2025-07-01     18 days   ← the largest gap in the corpus

    manifested but 404 at source (2 days)
      2022-11-10    20221110.export.CSV.zip
      2023-03-23    20230323.export.CSV.zip

The daily era should hold 4,921 days; GDELT's manifest lists 4,899 and 4,897 are on disk.
The days either side of every gap are present.

A missing file is not a quiet day. Read as zero, each would be the most extreme anomaly in fifty
years of data, and any anchoring whose positions happen to land there would score spectacularly on
an artefact.

The eighteen-day run matters most, and by more than a first estimate suggests. **The units of X are
the 400 SFO-BB node values, not a round 100-day step** — the nodes are irregular, 228 of the 399
consecutive pairs sit closer than 18 days, and the tightest is 0.09 days. So an instance can place
several positions inside that window, not one. Measured over the 36,001 day-resolution anchorings:

    at least one node inside the 18-day gap     13.7% of anchorings
    more than one                                4.0%
    worst case                                   6 nodes
    all 24 NULL days, at least one node         17.5% of anchorings, up to 7

One NULL read as zero is enough to carry a whole path's score; six would decide it.

**(b) One file was republished after the manifest was written.**

`20230322.export.CSV.zip` is 4,223,243 bytes on disk and on the server; the manifest says 4,223,252
with a different md5. Our copy is the currently published file and passes `unzip -t`. Any future
verification must let the **server** decide when it disagrees with the manifest, not the manifest.

**(c) The series is not stationary, and at 2013-04 it changes what it is measuring.**

Volume grows by two orders of magnitude, ~1,200 events/day in 1979 to ~220,000 in 2016. These are
artefacts of GDELT's history, not the world's, and they sit close to positions that matter: 2013–15
is dense in the whizz-kids sampling and 2015-04-30 is its Ztp.

Measured on the aggregate, the two largest steps are **not** the two named above:

| break | what it is | in the plot |
|---|---|---|
| **1996** | GDELT's source base widens | ~3× step, the largest in the series |
| **2006-01** | yearly files give way to monthly | ~2× step, and the noisiest era begins |
| **2013-04-01** | **the key changes — see below** | dip, then ~2× step |
| 2015-02-19 | GDELT 2.0 | modest |

The 2013-04 break is a change of quantity, not just of level, and this was missed until the files
were read:

- **1979-01-01 .. 2013-03-31** — 27 yearly and 87 monthly archives, partitioned by **SQLDATE**,
  the date the event is attributed to. DATEADDED here is a constant backfill stamp (20130203 /
  20130206) from GDELT's 2013 retrospective pass, so it carries nothing. The day must be SQLDATE.
- **2013-04-01 onward** — 4,897 archives, one per **ingestion day**. About 97% of rows carry that
  day's SQLDATE and the rest are backdated, sometimes by decades. The day must be the file's own
  date.

So the first era is *events attributed to this day*, the second is *events ingested on this day*.
Both are defensible daily series; they are not the same series. Anything spanning 2013-04 compares
across that seam.

Keying the daily era on the file rather than on SQLDATE is also what makes it robust to GDELT's
date-parser failures. On **2020-01-01**, 87,339 of 89,215 rows are dated 1920-01-01 — a two-digit
year read as the wrong century — and *not one row* carries 2020-01-01. Binned by SQLDATE that day
would read as near-empty and 1920-01-01 would carry a spike of 87k. Binned by file it is simply a
normal day, which it was.

**(d) The working week is 70% of the residual, and it aliases the sweep over Y.**

Found 2026-09-22 in the aggregate, and it is the most consequential of the four. Against a 91-day
rolling median in log space, day-of-week alone accounts for **70% of the residual sd**. A Sunday
runs at 0.57–0.66× a Wednesday, and the ratio drifts across the decades, so the correction has to
be local rather than a single global factor.

    weekday offset, log10, residual vs 91-day median

              all years          2016-2026
      Mon      ×0.983             ×0.927
      Tue      ×1.068             ×1.051
      Wed      ×1.081             ×1.088
      Thu      ×1.070             ×1.083
      Fri      ×1.009             ×1.012
      Sat      ×0.685             ×0.647
      Sun      ×0.656             ×0.571

Why this is a REVOTT problem and not just a time-series problem. The aliasing is entirely on the Y
side, and it is exact:

**One step of Y at day resolution is 0.01, which is one day, so it moves every node on the path by
one day at once.** The weekday of the whole path therefore rotates together with period 7 days —
period 0.07 in Y — and any statistic that averages the field over the path carries an exactly
period-7 component in Y, determined by one thing: the weekday histogram of the path.

Nothing analogous holds on the X side, and an earlier draft of this section claimed it did. The
units of X are the 400 node values; they are irregular (263 distinct gaps, most common 10.8 days,
with 252-day jumps through the set), so there is no fixed step in X and no argument about the sweep
can be built on one.

The histogram is not flat. It has no reason to be — the node values were not chosen against a
calendar — and measured, it is not:

    Y = 24.50   Mon 52  Tue 71  Wed 80  Thu 54  Fri 42  Sat 57  Sun 44    flat would be 57.1

So the path is Tuesday/Wednesday-heavy and Friday/Sunday-light, and the same tilt appears at 34.918,
82.80 and 85.32. The consequence, computed exactly in `gdelt/weekday_alias.py`:

    ripple in mean-z across the 7 rotations      0.217 z
    sampling sd of mean-z over 400 positions     0.050 z
    ratio                                        4.3x   (4.5x at Y = 34.918)

**The weekday artefact is four times the noise floor of the statistic it contaminates.** An
uncorrected sweep would be reading the working week, at an amplitude that buries anything the field
itself could say.

And the protection an earlier draft claimed — that a sum over all 400 keys is near-balanced because
400 = 7×57 + 1 — is false. Balance depends on the weekday histogram, not on the count; the full
400-key path is exactly what carries the 0.217 z ripple. Nothing is immune: not the sum, not the
pre-registered few X of §2, not any max, run-length or extremum count.

Worse for the derivative-based statistics of §3: in a series with a 1.65× weekly swing, "is this
position a local maximum" largely means "is this a Wednesday", and sign changes in the derivative
are mostly Friday→Saturday.

---

So: **nothing raw.** Everything against a rolling local baseline, in log space, with the
breakpoints marked, the weekday removed, and the NULLs propagated as NULL. That is what `field.py`
does, and the `z` column is the result. Derivative-based statistics are better than level ones,
being less exposed to drift — but only after the weekday correction, which they need more than the
level ones do, not less.

---

## 6. How this meets REVOTT

REVOTT is one coordinate and two additive shifts on it — section 1 above. Because a date is `origin + TNLDY days`, **scanning Y is sliding an integer offset over a daily
series.** No calendar arithmetic per anchoring. One unit of Y is exactly 100 days.

The two operations, as REVOTT is actually worked:

- **hold Y fixed, sweep X across the SFO** — the primary mode. `revott sweep --y 24.50 --csv`
  emits x, tnldy, date, year, framework text for every key.
- **a named few X against a fixed Y** — the pre-registered mode. Name the positions before looking.

**There is no set of 265.** That number was an artifact of the earlier matching process. The domain
is X, continuous; the 400 keys are structure standing on it. Nothing in the GDELT work should be
conditioned on whether evidence was once found near a position.

---

## 7. The statistical trap, stated before any measurement

Y at day resolution over [−147.60, 212.40] gives **36,000 distinct anchorings**. Sweep them, take
the best, and you will find something extraordinary from noise alone, with certainty.

There is also an **invariance**: position X in instance Y falls on the same date as X′ in Y′
whenever Y + X = Y′ + X′. Sliding the anchor one unit and the position one unit the other way lands
in the same place — so scanning Y *is* a shift test, and the null falls out of the same sweep
rather than needing separate construction.

The discipline, in order:

1. **Fix the statistic before scanning.** Chosen in advance, not after seeing results.
2. **Score the named instances first** — Y = 24.50, 34.918, 82.80, 85.32 — as pre-registered
   hypotheses.
3. **Then the full sweep**, and report the named instances' **percentile against all 36,000**, never
   a raw score or a sigma.
4. **Null from the sweep itself**, plus explicit random anchorings as a cross-check.

The honest headline is never "Y = 24.50 scores 3.7σ". It is "Y = 24.50 ranks 412th of 36,000" — or
"first", which would be worth everything.

### Which statistics are admissible

Step 1 above is the whole game, and two facts constrain it. Both are computed in
`gdelt/weekday_alias.py`, from the calendar and the DAG alone — no field data, so neither can be
tuned after seeing a result.

**The DAG.** `revott/data/keys.json` already carries it, reconciled against
`nth_agent_instances/SFO_BB_399_merged_with_WAM_successors.xlsx`: 400 nodes, 704 edges, a single
root at −147.60 and a single sink at 212.40. 399 of those edges are the backbone — every
consecutive-in-x pair — and **305 are long-range**. Four edges state a weight that disagrees with
`target − source`; `sfo.py` exposes them as `disputed()` and they should be settled before anything
leans on edge weights:

    -21.1853 -> 11.6919   stated 2.1232   implied 32.8772
       -3.31 -> 29.528    stated 1.81     implied 32.838
      13.318 -> 17.32     stated 3.6      implied 4.002
       23.41 -> 29.528    stated 3.6      implied 6.118

The long-range gap spectrum is where the structure shows: 360 days ×23, 181 ×14, 179 ×14,
**252 ×13** (36 weeks exactly), 483 ×8 (69 weeks), 10.8 ×11. The 252 of §2 is an SFO edge; the 5830
and 6082 are not — they are between-instance relations and appear nowhere in this DAG, which is
what §2 means by calling them relations rather than derivations.

**A mean gradient over the backbone is empty, not robust.** The backbone visits all 400 nodes in
order, so for *any* function f,

    mean over backbone edges of ( f(target) − f(source) )  =  ( f(sink) − f(root) ) / 399

It telescopes. Verified as an exact identity, not an approximation. Its apparent immunity to the
weekday artefact — 0.1× the noise floor, far the best figure in the table — is that emptiness. A
statistic that cannot see the 398 interior nodes cannot be contaminated by them, and cannot be
informed by them either.

Everything that does carry information is exposed, at Y = 24.50:

    statistic                        n     ripple    floor    ratio
    mean z over nodes              400     0.2166   0.0500     4.3x
    mean gradient, backbone        399     0.0069   0.0708     0.1x   telescopes; empty
    mean |gradient|, backbone      399     0.1710   0.0708     2.4x
    mean |gradient|, long-range    305     0.1232   0.0810     1.5x
    mean |gradient|, all edges     704     0.1138   0.0533     2.1x

So: **no statistic escapes the weekday artefact by being clever about the DAG.** The correction has
to be in the field, which is what `field.py`'s `z` column is for, and any statistic proposed for
step 1 should be run through `weekday_alias.py` before it is fixed — a ratio near 1 means the
artefact is at the noise floor, a ratio near 0 means the statistic is empty, and both are
disqualifying for opposite reasons.

The permutation machinery for this is still to be written. It is a small thing next to getting the
field right, and it should live in `gdelt/` beside the rest.

---

## 8. The aggregate — built 2026-09-22

50 GB collapsed to **one row per day** since 1979. Every scan now runs in memory in seconds and the
corpus is not touched again. In `revott/gdelt/`:

    build.sh                      the driver — ./build.sh, ~4 min wall on 14 jobs
      agg_one.sh                  one archive  -> per-day partial rows      bash + awk
      merge_aggregate.py          partials     -> dense daily series        stdlib only
      field.py                    daily series -> the corrected field       numpy only
    weekday_alias.py              §5d and §7, computed exactly — run it     numpy only
    overlay.py                    REVOTT over the field, one row per node   numpy only
    sweep.py                      all 36,001 anchorings, for ranking        numpy only
    plot_series.py                the picture                               needs matplotlib
    gdelt_daily_1979_2026.csv     17,430 rows · 3.0 MB · the whole instrument
    series.png                    volume, residual, and the weekly cycle

**The corpus is read, never extracted.** Each archive streams through `unzip -p` into awk; nothing
is written beside the zips and the 50 GB stays compressed. Re-running `build.sh` is safe and
reproduces the file exactly.

    date, present, era, n_events, n_mentions, n_articles, n_sources,
    avg_tone, avg_goldstein, n_root, q1_verb_coop, q2_mat_coop,
    q3_verb_conf, q4_mat_conf, offday_rows, breakpoint, source,
    level_log10, dow_adj, resid, scale, z

Three states, and they are not the same: `present=1, n_events>0`; `present=1, n_events=0` (a file
covers the day and carried nothing); `present=0` with every field empty (no file — the 24 days of
§5a). **`z` is the instrument** — log10 volume, minus a centred 91-day median, minus a local
weekday offset, over a local 365-day sd. It is defined on 17,406 of 17,430 days, mean −0.08, sd
1.00, range −13.1 to +6.7.

Two departures from the column list this section originally specified:

- **`n_tech_events` was dropped.** GDELT 1.0's export schema carries no technology flag, and every
  proxy available — actor type codes, CAMEO root codes — would have been a definition invented here
  and then measured as though it were in the data. If a tech subset is wanted it should be defined
  first, in the open, and justified on its own.
- **The quad-class counts and `avg_goldstein` were added**, being free at aggregation time and what
  the derivative-based statistics of §3 actually need: a path can have a flat volume and still turn
  over in composition.

The plot is made and **the series' pathologies were visible first, as intended** — the aggregate
overturned §5 twice before anything was scored through it. That is the section to read, not this one.

There is also `~/gharchive_raw_2011_2014` — 95 GB, complete hourly GH Archive, 2011-02-12 to
2014-12-31, already on disk. For a ledger about computing it is arguably the better denominator:
GDELT measures that journalists wrote something, GH Archive measures what was built. Its window
coincides with the densest region of the whizz-kids sampling. The machinery to read it already
exists in `~/pdp-causal-agent/`: `build_repo_hour_index.py`,
`scan_repo_events_catalog_checkpointed.py`, `extract_repo_events_from_index.py`.

---

## 9. The first measurement — 2026-09-22

**Scope, before anything else.** This measures **four values of Y**, at the **100D scale on the raw
position**. That is not the REVOTT structure and must not be read as it:

- §2 names eleven readings at four scales and says this implementation traverses one of them. A
  slice, never to be written as though it were the structure.
- The **instance family is not established**. §1 identifies `CANONICAL READOUT — EQUATION OF THE
  SHIFTING ZEROES.xlsx` as the direct source for it and for the YGADi reading, and that workbook is
  still unread. The domain line there — 85.68 / 85.32 / 84.80 / 83.60 / 82.80 ≥ Y ≥ 0 — already
  names shifting zeroes this section does not touch.
- The four Y values scored below are the four §7 step 2 happens to list. They are a starting point
  someone wrote down, not an enumeration of anything.

So: a negative reading below is a negative reading **about those four Y at that one scale**, and
carries no weight against REVOTT. Read it as the instrument's first run, not as a finding about the
system.

REVOTT laid over GDELT, per node. `gdelt/overlay.py [Y]` writes one row per node — x, TNLDY, date,
weekday, `z`, its percentile against all 17,406 present days, whether the day is a local extremum,
and the framework text standing there. `gdelt/sweep.py` scores all 36,001 anchorings the same way
so a named one can be ranked. No p-values anywhere: a percentile against the field, and a rank
against the sweep.

**Coverage first, because it bounds what can be asked.** The path spans 36,000 days — 98.6 years —
and the field spans 47.7. No anchoring can ever place all 400 nodes in the field.

    Y = 24.50    366 of 400 scored   path 1974-12-01 .. 2073-06-24
    Y = 34.918   330 of 400          path 1977-10-08 .. 2076-05-01
    Y = 82.80     78 of 400          path 1990-11-17 .. 2089-06-10   not testable
    Y = 85.32     54 of 400          path 1991-07-27 .. 2090-02-17   not testable

**Two of the four named instances cannot be tested against GDELT at all.** Their paths start too
late. This is not a result about them; it is the field running out.

**Y = 24.50, ranked among the 13,781 anchorings that cover at least 300 nodes:**

    statistic                        value            rank
    mean z over nodes               -0.0144      #4,781 / 13,781
    rate of nodes at pct >= 99.5     0.0164  (6/366)   #62 / 13,781
    rate of nodes at pct >= 99.0     0.0164      #942 / 13,781
    rate of nodes at pct <= 1.0      0.0109    #5,317 / 13,781
    rate of nodes at pct <= 0.5      0.0000       tied last
    rate of local extrema            0.2596    #7,316 / 13,781

Five of the six sit where anything would. The node readings themselves are the field's own
distribution: mean −0.014 sd 1.015 against the field's −0.027 and 1.000. Local extrema fall at
26.0% of nodes against a field base rate of 26.1%.

**The sixth, #62, does not survive inspection, and it is worth saying exactly how it fails.**

- Its neighbours rank #3,430 and #3,467. One day either side of 24.50 and the feature is gone.
- What separates rank #62 from rank #3,430 is **four nodes crossing a threshold** — 6 of 366 versus
  2 of 366. It is the discreteness of a rare-event count, and the field is autocorrelated enough
  that a real feature would not vanish under a one-day shift.
- The top 62 anchorings form **42 separate blocks**. Y = 24.50 is one of 42 comparable isolated
  spikes in the same sweep.
- The sweep's own autocorrelation (integrated time ~4 days) puts roughly 3,561 effectively
  independent anchorings in those 13,781, so #62 is near the top 2% of independent draws — and it
  is one statistic of six fixed before any anchoring was ranked, of which the other five are flat.

**The reading is negative, within the scope stated at the head of this section.** At Y = 24.50, on
the 100D scale on raw position, with 366 of 400 nodes scored, that path is not distinguishable from
an arbitrary path through the same field. The instrument can return negative, which §2 requires of
it. It says nothing about the other scales, the conjugate readings, or the instances the CANONICAL
READOUT enumerates.

**What the measurement corrected on the way.** The first overlay's low tail was six nodes in
Dec 20 – Jan 6. The annual cycle was still in the field — Jan 1 averaged z = −4.0, Dec 25 z = −3.6,
every year, with the day-of-year means carrying **47% of the residual sd**. A centred 91-day median
straddles the holiday fortnight with eleven normal weeks and leaves it almost intact. `field.py`
now removes a day-of-year offset matched on the exact calendar date across ±8 years, which takes
67% of it out and makes Jan 1 unremarkable. Every number in this section is post-correction. Like
the weekday of §5d, it aliases the sweep — one Y step is one day, so day-of-year rotates with it,
at period 3.6524 in Y.

**Not independent, and the readout says so.** The 366 scored nodes fall on 358 distinct dates;
eight pairs share a date outright, and tight clusters see correlated days. The counts above are
counts of nodes, not of independent observations.

`overlay_Y24p5.csv` is the per-node table. It is the thing to read: the six nodes above pct 99.5
and the four below pct 1 are listed there with their framework text, and they are what a negative
result looks like from the inside.

---

## 10. The GitHub strategy

**Two repositories, both private, both under the `nth-member` org, neither containing the corpora.**

| repo | holds | status |
|---|---|---|
| `nth-member/whizzkids-witness` | one instance's witness: evidence, findings, the report | pushed; 7 commits unpushed |
| `revott` (`~/revott`) | the coordinate system, the SFO, the readings | local only, 2 commits, **not yet pushed** |

**The corpora are never committed.** 53.7 GB of GDELT and 95 GB of GH Archive stay on disk, outside
git, reproducible from source. What goes in the repo is the **aggregate** — a few hundred KB — plus
the code that produced it and the manifest and checksums that pin which corpus it came from.

**Identity.** All commits authored `nth-member <nth-member@users.noreply.github.com>`, scoped with
`git config --local`; the global config is untouched and every other repository still pushes as the
account owner. No real name, email or home path in any tracked file. Org membership is Private.

**A push needs a token with both `repo` and `workflow` scopes** — `public_repo` is not enough for a
private repo, and a repo containing a workflow file needs `workflow` as well.

**Stay private until after the viva.** The vocabulary here — SFO-BB, TNLDY, dysi, REVOTT, the
parable — is unique and will appear in a named dissertation. Going public would undo the pseudonym
by correlation rather than by metadata, and public repos are announced through GitHub's event
firehose rather than discovered. GitHub Pages on a private repo needs a paid plan, and a Pages site
built from a private repo is itself public; the artifact links are the sharable surface.

**When REVOTT is pushed**, it should carry `data/keys.json`, `data/readings.json`, the package and
the rendered pages — all small — and gitignore anything derived from the corpora beyond the daily
aggregate.

---

## 11. Open

- **The first measurement is done and it is negative for four Y at one scale** (§9). It is not a
  reading on REVOTT. Y = 82.80 and 85.32 could not be tested at all — too few nodes inside the field.
- **The instance family is still inferred, not taken from source.** `CANONICAL READOUT — EQUATION
  OF THE SHIFTING ZEROES.xlsx` remains unread, and until it is, any list of instances — including
  the four in §7 step 2 — is provisional. This is the blocking item for widening §9 beyond a slice.
- The other three scales and the eleven conjugate readings of §2 are untouched by §9.
- The six statistics of §9 were fixed before ranking, but they are not the only defensible ones.
  Anything new must be declared before it is run, and run through `weekday_alias.py` first.
- The permutation test of §7 is unwritten.
- The four disputed edges of §7 are unsettled. `sfo.py` exposes them as `disputed()`; nothing yet
  leans on edge weights, so nothing is wrong today, but any weighted statistic would inherit them.
- `revott` is not pushed; `whizzkids-witness` has 7 commits unpushed.
- The witness still truncates TNLDY with an `int()` cast — a real bug, losing sub-day precision.
- The witness's `axis.py` still models each anchoring as a separate epoch, when REVOTT has one
  origin and two additive shifts. It should call into `revott.core`.
- The witness is still organised around the 265. That set is a result, not a structure.
- No live Anthropic API call has ever been made from any of this.
- `CANONICAL READOUT — EQUATION OF THE SHIFTING ZEROES.xlsx` is unread. It states the inverse
  transforms and enumerates the zeroes; reading it would settle the YGADi reading and the full
  instance family, both of which are currently inferred rather than taken from source.
- The GH Archive corpus of §8 is untouched. If it is aggregated, the weekday problem of §5d is
  *worse* there, not better: commits are far more weekday-concentrated than news is.
- The four eras of §5c are compared through one `z` column as though they were one series. They are
  not. Whether a path may cross 2013-04 at all is an open methodological question, and the honest
  answer may be to score only within an era.
