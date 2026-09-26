#!/bin/bash
# Bring everything up to date with GDELT, from one command.
#
#   ./refresh.sh              fetch new days, rebuild what they touch, commit
#   ./refresh.sh --check      say what is new and stop; changes nothing
#   ./refresh.sh --push       as above, then push both repos
#
# Idempotent. Run it as often as you like: with no new days it stops after the
# manifest and rebuilds nothing. Nothing is ever deleted, and the corpus is
# never extracted -- every archive is read by streaming through `unzip -p`.
#
# The short-circuit matters. Stage 4 rebuilds the whole daily aggregate, because
# field.py's level and scale are rolling windows over the entire series and a
# new day shifts the tail of both. That costs ~4 minutes, so it runs only when
# archives actually arrived. Stages 1-3 are incremental and cost seconds.
#
# Two archives will always show as listed-but-absent: 20221110 and 20230323 are
# in GDELT's index and 404 on its server. They are not new days and not an
# error. They must keep reading as NULL, never zero.
set -euo pipefail

CORPUS="${CORPUS:-$HOME/gdelt_raw_1979_2026}"
URLS="${URLS:-$HOME/gdelt-urls}"
MEMBER="${MEMBER:-$HOME/member}"
REVOTT="$(cd "$(dirname "$0")/.." && pwd)"

MODE=run
case "${1:-}" in
  --check) MODE=check ;;
  --push)  MODE=push ;;
  "")      ;;
  *) echo "usage: $0 [--check|--push]" >&2; exit 2 ;;
esac

say(){ printf '\n\033[1m%s\033[0m\n' "$*"; }
have(){ ls "$CORPUS"/files/*.zip 2>/dev/null | wc -l; }

# ---- 1. the manifest ---------------------------------------------------------
# GDELT retired filesizes.txt and md5sums.txt -- both 404 now -- so they are
# rebuilt from the index page, which still lists every archive with its MD5.
# Without this the corpus looks complete forever and no later stage ever runs.
say "1. manifest"
if [ "$MODE" = check ]; then
  python3 "$REVOTT/gdelt/manifest.py" "$CORPUS" --check
  say "check only — nothing changed"
  exit 0
fi
python3 "$REVOTT/gdelt/manifest.py" "$CORPUS"

# ---- 2. fetch ----------------------------------------------------------------
say "2. fetch"
was=$(have)
python3 "$CORPUS/fetch.py" || true      # a 404 on a known-absent day is not fatal
now=$(have)
echo "   archives: $was -> $now  (+$((now - was)))"

if [ "$now" -eq "$was" ]; then
  say "already current — nothing arrived, nothing rebuilt"
  exit 0
fi

# ---- 3. the day URLs, incremental --------------------------------------------
say "3. day sources  (incremental — an existing day is skipped in 2ms)"
d0=$(ls "$URLS/docs/days" 2>/dev/null | wc -l)
"$URLS/build.sh" "$CORPUS"
d1=$(ls "$URLS/docs/days" | wc -l)
echo "   day files: $d0 -> $d1  (+$((d1 - d0)))"

# ---- 4. the aggregate, full --------------------------------------------------
say "4. daily aggregate  (full rebuild — rolling baselines span the whole series)"
"$REVOTT/gdelt/build.sh" "$CORPUS"
python3 "$REVOTT/docs/build_data.py"

# ---- 4b. the member ----------------------------------------------------------
# REVOTT's numerator lives in its own repository and site, ~/member ->
# nth-member.github.io/member/. It writes its journal entry for the newest day,
# then rebuilds the site's data. Its failure never fails the refresh.
if [ -d "$MEMBER" ]; then
  say "4b. the member"
  ( python3 "$MEMBER/member.py" && python3 "$MEMBER/build.py" ) \
    || echo "   member: FAIL — the refresh itself is unaffected"
fi

# ---- 5. commit ---------------------------------------------------------------
last=$(ls "$URLS/docs/days" | tail -1 | sed 's/\.json$//')
say "5. commit  (through $last)"
# Stage only the paths this script produces. `git add -A` here would sweep up
# whatever else happens to be uncommitted in either repo -- a half-finished edit
# to the app, a draft in the handover -- and commit it under a message about
# days, then push it. Anything else is left alone and reported.
paths_for(){
  case "$1" in
    "$URLS")   echo "docs/days docs/range.json" ;;
    "$REVOTT") echo "gdelt/gdelt_daily_1979_2026.csv docs/data" ;;
    "$MEMBER") echo "docs" ;;
  esac
}
for r in "$URLS" "$REVOTT" "$MEMBER"; do
  [ -d "$r/.git" ] || continue
  own=$(paths_for "$r")
  # shellcheck disable=SC2086
  git -C "$r" add -- $own
  other=$(git -C "$r" status --porcelain | grep -v '^[MARD]' || true)
  if ! git -C "$r" diff --cached --quiet; then
    git -C "$r" commit -q -F - <<MSG
Days through $last

Refreshed from GDELT: +$((now - was)) archives, +$((d1 - d0)) day files.

The tail of the field is provisional. field.py's level and scale are centred
windows, so the most recent months are computed against windows that run off
the end of the data and firm up as days arrive.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
    echo "   $(basename "$r"): $(git -C "$r" log --oneline -1)"
  else
    echo "   $(basename "$r"): nothing to commit"
  fi
  if [ -n "$other" ]; then
    echo "   $(basename "$r"): left alone, not mine to commit —"
    printf '%s\n' "$other" | sed 's/^/     /'
  fi
done

# ---- 6. push -----------------------------------------------------------------
if [ "$MODE" = push ]; then
  say "6. push"
  for r in "$URLS" "$REVOTT" "$MEMBER"; do
    [ -d "$r/.git" ] || continue
    echo "   $(basename "$r") …"
    git -C "$r" push
  done
fi

say "done — through $last"
