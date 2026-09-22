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
so carries no information. GDELT has a continuous daily series from **1979-01-01**, so the question
becomes *what is the state of the field at this position, and its derivative?* That is answerable,
and it can come back negative.

This replaced an earlier approach that had to be withdrawn. The SFO-BB ledger's most common form of
evidence was "a report was published that day", 95 of 96 same-day items drawn from one archive that
publishes every weekday — true of almost any date in its range. Naming those domains as preferred
sources would have trained a witness to reproduce exactly that. See the whizz-kids repo's commit
`003cb08`.

The framing that follows from it: the daily series is a **scalar field over time**; an instance's
positions are a **path** through it; the backbone orders that path. The testable question is
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
    └── (no aggregate yet)

Fetched in 1.14 h at ~11 MB/s. Verified: **5,011 md5-exact, 1 restated, 2 absent, 0 bad.**

**Re-running `fetch.py` is safe at any time.** A file whose size matches is skipped, a partial is
continued, nothing is deleted. `verify.py` is read-only.

---

## 5. Three facts about this corpus that are correctness issues, not trivia

**(a) Two days are missing, and they must read as NULL, never zero.**

    2022-11-10    20221110.export.CSV.zip — 404 at source
    2023-03-23    20230323.export.CSV.zip — 404 at source

Both are listed in GDELT's own manifest and absent from their server; the days either side are
present. A missing file is not a quiet day. Read as zero, each would be the most extreme anomaly in
fifty years of data, and any anchoring whose positions happen to land there would score
spectacularly on an artefact.

**(b) One file was republished after the manifest was written.**

`20230322.export.CSV.zip` is 4,223,243 bytes on disk and on the server; the manifest says 4,223,252
with a different md5. Our copy is the currently published file and passes `unzip -t`. Any future
verification must let the **server** decide when it disagrees with the manifest, not the manifest.

**(c) The series is not stationary and has collection discontinuities.**

Volume grows by orders of magnitude across the series, and the 2013-04 daily-file transition and
the Feb-2015 2.0 changeover are visible as step changes. These are artefacts of GDELT's history,
not the world's. They sit close to positions that matter: 2013–2015 is dense in the whizz-kids
sampling and 2015-04-30 is its Ztp.

So: **nothing raw.** Everything against a rolling local baseline, in log space, with the
breakpoints marked and either excluded or explicitly modelled. A z-score of daily volume against
its own trailing 90-day distribution is the minimum defensible statistic; derivative-based ones are
better, being less exposed to level drift.

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

`~/pdp-causal-agent/build_step4h_tih_permutation_test.py` already handles this shape of problem.

---

## 8. Next step: the aggregate

Collapse 53.7 GB to **one row per day** since 1979 — a few hundred KB — after which every scan runs
in memory in seconds and the corpus is never touched again.

    date | n_events | n_mentions | avg_tone | n_sources | n_tech_events | present

`present` is the flag that keeps 2022-11-10 and 2023-03-23 out of every statistic. Mark the 2013-04
and Feb-2015 breakpoints in the same pass.

**Plot the series with the breakpoints marked before scoring anything through it.** The field's own
pathologies should be visible first.

There is also `~/gharchive_raw_2011_2014` — 95 GB, complete hourly GH Archive, 2011-02-12 to
2014-12-31, already on disk. For a ledger about computing it is arguably the better denominator:
GDELT measures that journalists wrote something, GH Archive measures what was built. Its window
coincides with the densest region of the whizz-kids sampling. The machinery to read it already
exists in `~/pdp-causal-agent/`: `build_repo_hour_index.py`,
`scan_repo_events_catalog_checkpointed.py`, `extract_repo_events_from_index.py`.

---

## 9. The GitHub strategy

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

## 10. Open

- The aggregate is not built. Nothing has been measured.
- `revott` is not pushed; `whizzkids-witness` has 7 commits unpushed.
- The witness still truncates TNLDY with an `int()` cast — a real bug, losing sub-day precision.
- The witness's `axis.py` still models each anchoring as a separate epoch, when REVOTT has one
  origin and two additive shifts. It should call into `revott.core`.
- The witness is still organised around the 265. That set is a result, not a structure.
- No live Anthropic API call has ever been made from any of this.
- `CANONICAL READOUT — EQUATION OF THE SHIFTING ZEROES.xlsx` is unread. It states the inverse
  transforms and enumerates the zeroes; reading it would settle the YGADi reading and the full
  instance family, both of which are currently inferred rather than taken from source.
