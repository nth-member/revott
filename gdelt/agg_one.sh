#!/bin/bash
# Aggregate one GDELT zip to per-day partial rows on stdout.
#
# Two eras, two keys, because GDELT partitions them differently:
#   1979-01-01 .. 2013-03-31   yearly/monthly files, partitioned by SQLDATE (col 2).
#                              DATEADDED is a constant backfill stamp (20130203/06)
#                              and carries no information, so the day must be SQLDATE.
#   2013-04-01 ..              one file per ingestion day. ~97% of rows carry that
#                              day's SQLDATE but the rest are backdated, and on some
#                              days GDELT's date parser fails wholesale (2020-01-01
#                              puts 87k of 89k rows on 1920-01-01). So the day is the
#                              file's own date, and off-day rows are counted, not binned.
#
# Columns 1-57 are identical in both eras; daily files add SOURCEURL as 58.
set -euo pipefail
f="$1"; b="${f##*/}"
case "$b" in
  [0-9][0-9][0-9][0-9].zip)                   mode=sqldate; period="${b%.zip}" ;;
  [0-9][0-9][0-9][0-9][0-9][0-9].zip)         mode=sqldate; period="${b%.zip}" ;;
  [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].export.CSV.zip) mode=fileday; period="${b:0:8}" ;;
  *) exit 0 ;;   # MASTERREDUCED and anything else: not part of the series
esac

unzip -p "$f" | awk -F'\t' -v MODE="$mode" -v PERIOD="$period" -v SRC="$b" '
  {
    if (MODE == "fileday") { d = PERIOD; if ($2 != PERIOD) off++ }
    else {
      d = $2
      if (d !~ /^[12][0-9]{7}$/) { bad++; next }
      if (substr(d, 1, length(PERIOD)) != PERIOD) outp[d]++
    }
    n[d]++
    men[d] += $32; art[d] += $34; src[d] += $33
    tone[d] += $35; gold[d] += $31
    if ($26 == 1) root[d]++
    q = $30 + 0; if (q >= 1 && q <= 4) qq[d, q]++
    if (NF != nf_seen) { nf_seen = NF; nfs[NF] = 1 }
  }
  END {
    nfl = ""; for (k in nfs) nfl = nfl (nfl ? "," : "") k
    for (d in n)
      printf "%s\t%s\t%s\t%d\t%d\t%d\t%d\t%.6f\t%.6f\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n",
        d, MODE, SRC, n[d], men[d], art[d], src[d], tone[d], gold[d],
        root[d], qq[d,1], qq[d,2], qq[d,3], qq[d,4],
        (MODE == "fileday" ? off + 0 : outp[d] + 0), bad + 0, nfl, PERIOD
  }
'
