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
PARTIALS="$(mktemp)"; trap 'rm -f "$PARTIALS"' EXIT

echo "reading $CORPUS/files ($(ls -1 "$CORPUS/files"/*.zip | wc -l) archives, $JOBS jobs)"
( cd "$CORPUS/files" && ls *.zip | xargs -P "$JOBS" -n 1 "$HERE/agg_one.sh" ) > "$PARTIALS"
echo "partial day-rows: $(wc -l < "$PARTIALS")"

python3 "$HERE/merge_aggregate.py" "$PARTIALS" "$OUT"
python3 "$HERE/field.py" "$OUT"
echo "done -> $OUT"
