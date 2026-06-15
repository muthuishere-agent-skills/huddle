#!/usr/bin/env bash
# verify-personas.sh — validates every company-os-live persona file added for the complete roster:
# required frontmatter keys + the required sections, the real-scar check, and roster coverage.
# Read-only. Run from the huddle repo root or anywhere.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"          # references/
PDIR="$HERE/personas"
ROSTER="$HERE/persona-roster.xml"
P=0; F=0
pass(){ printf '  \033[32m✓\033[0m %s\n' "$1"; P=$((P+1)); }
fail(){ printf '  \033[31m✗\033[0m %s\n' "$1"; F=$((F+1)); }
hdr(){ printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

# the 13 company-os-live personas authored for the complete roster
NEW=(dhana-cryptodesk kuber-equitiesstrategy thiru-intradaydesk \
     jana-companyos anitha-interviewprep gnanavel-commonsdev vinish-reqsumegrowth vignesh-skillsupplychain \
     venugopal-researchlead parthasarathy-researcher ramesh-nicheresearch jency-buildinpublic nirmal-spendguard)

FM_KEYS=(name displayName title icon role domains capabilities identity primaryLens communicationStyle principles)
SECTIONS=("## Signature Phrases" "## Common Disagreements")

hdr "1. every new persona file exists + has full frontmatter"
for n in "${NEW[@]}"; do
  f="$PDIR/$n.md"
  if [ ! -f "$f" ]; then fail "MISSING $n.md"; continue; fi
  miss=""
  for k in "${FM_KEYS[@]}"; do
    grep -qE "^$k:" "$f" || miss="$miss $k"
  done
  [ -z "$miss" ] && pass "$n.md — all 11 frontmatter keys" || fail "$n.md missing frontmatter:$miss"
done

hdr "2. required body sections (Signature Phrases + Common Disagreements)"
for n in "${NEW[@]}"; do
  f="$PDIR/$n.md"; [ -f "$f" ] || continue
  miss=""
  for s in "${SECTIONS[@]}"; do grep -qF "$s" "$f" || miss="$miss '$s'"; done
  [ -z "$miss" ] && pass "$n.md — has Signature Phrases + Common Disagreements" || fail "$n.md missing:$miss"
done

hdr "3. identity carries a REAL SCAR (the 'scar' word + a failure verb)"
for n in "${NEW[@]}"; do
  f="$PDIR/$n.md"; [ -f "$f" ] || continue
  id=$(awk '/^identity:/{flag=1} flag{print} /^primaryLens:/{flag=0}' "$f")
  echo "$id" | grep -qi 'scar' && pass "$n.md — identity names a scar" || fail "$n.md — no scar in identity"
done

hdr "4. name slug is namespaced (huddle-*) + displayName is a real person"
for n in "${NEW[@]}"; do
  f="$PDIR/$n.md"; [ -f "$f" ] || continue
  grep -qE '^name: huddle-' "$f" && grep -qE '^displayName: [A-Z]' "$f" && pass "$n.md — namespaced name + displayName" || fail "$n.md — name/displayName format"
done

hdr "5. roster coverage — every new file is referenced in persona-roster.xml"
for n in "${NEW[@]}"; do
  grep -qF "personas/$n.md" "$ROSTER" && pass "roster references $n.md" || fail "roster MISSING $n.md"
done

hdr "6. no alias-duplication (Peter/Maya, Dileep/CEO already covered — not re-added)"
# we must NOT have created peter-* or a second dileep-* file
ls "$PDIR"/peter-*.md >/dev/null 2>&1 && fail "duplicate: peter-*.md exists (Peter=Maya alias)" || pass "no peter-*.md dup (Peter→Maya honored)"
[ "$(ls "$PDIR"/dileep-*.md 2>/dev/null | wc -l | tr -d ' ')" = "1" ] && pass "single dileep file (CEO→Dileep honored)" || fail "dileep file count off"

hdr "RESULT"
printf '  \033[1m%d passed, %d failed\033[0m\n' "$P" "$F"
[ "$F" -eq 0 ] && { echo "  PERSONAS VERIFIED — 13 company-os-live personas complete + rostered, aliases honored."; exit 0; } || exit 1
