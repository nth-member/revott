#!/bin/bash
# Build the daily aggregate from the GDELT corpus.
#
#   ./build.sh [CORPUS_DIR]        default ~/gdelt_raw_1979_2026
#
# The corpus is read, never extracted: agg_one.sh streams each archive through
# `unzip -p` into awk, so nothing is ever written next to the zips and the 50 GB
# stays compressed. Re-running is safe and produces the same file.
#
# Three stages, each usable alone:
#   agg_one.sh          one archive  -> per-day partial rows          (bash + awk)
#   merge_aggregate.py  partials     -> dense daily series, NULLs marked  (stdlib)
#   field.py            daily series -> + level, weekday, scale, z    (numpy)
#
# Only plot_series.py needs anything beyond the system python.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="${1:-$HOME/gdelt_raw_1979_2026}"
JOBS="${JOBS:-14}"
OUT="$HERE/gdelt_daily_1979_2026.csv"
PARTS="$(mktemp -d)"; trap 'rm -rf "$PARTS"' EXIT
PARTIALS="$PARTS/all.tsv"

# One file per archive, joined only once every job has finished. Parallel jobs
# writing one shared output interleave their buffered writes mid-line; nothing
# has been corrupted by it (a race-free rebuild matched this file cell for
# cell on 2026-09-25), but nothing guaranteed it either.
echo "reading $CORPUS/files ($(ls -1 "$CORPUS/files"/*.zip | wc -l) archives, $JOBS jobs)"
( cd "$CORPUS/files" && ls *.zip |
    PARTS="$PARTS" HERE="$HERE" xargs -P "$JOBS" -n 1 sh -c '"$HERE/agg_one.sh" "$0" > "$PARTS/$0.tsv"' )
cat "$PARTS"/*.zip.tsv > "$PARTIALS"
echo "partial day-rows: $(wc -l < "$PARTIALS")"

python3 "$HERE/merge_aggregate.py" "$PARTIALS" "$OUT"
python3 "$HERE/field.py" "$OUT"
echo "done -> $OUT"
