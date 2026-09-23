#!/usr/bin/env bash
# contact-sheet.sh — build a drift-audit contact sheet.
#
# Extracts a representative frame from each shot, puts the canon frame first,
# and tiles them into one image so slow character drift becomes visible.
#
# Run this every 8-10 accepted shots. Drift is invisible shot-to-shot and
# obvious in aggregate.
#
# Usage:
#   ./contact-sheet.sh <canon-frame.png> <shots-dir> [output.jpg] [grab-seconds]
#
# Example:
#   ./contact-sheet.sh refs/mara_canon.png shots/ audit_mara_s01.jpg 1.5
#
# Requires: ffmpeg, ImageMagick (montage)

set -euo pipefail

CANON="${1:?usage: contact-sheet.sh <canon-frame> <shots-dir> [output] [grab-seconds]}"
SHOTS_DIR="${2:?missing shots directory}"
OUT="${3:-contact-sheet.jpg}"
GRAB_AT="${4:-1.0}"   # seconds into each clip to sample

command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }
[ -f "$CANON" ]     || { echo "canon frame not found: $CANON" >&2; exit 1; }
[ -d "$SHOTS_DIR" ] || { echo "shots dir not found: $SHOTS_DIR" >&2; exit 1; }

# Every tile is normalised to one canvas size. ffmpeg's filter graph cannot
# cope with frames of differing dimensions arriving on the same input.
TILE=400
NORM="scale=${TILE}:${TILE}:force_original_aspect_ratio=decrease,pad=${TILE}:${TILE}:(ow-iw)/2:(oh-ih)/2:color=0x111111"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Canon frame goes first, so every comparison is against it rather than
# against the previous shot. Re-encoded rather than copied: files in the
# wild are often JPEGs wearing a .png extension, and ffmpeg trusts the
# extension.
ffmpeg -loglevel error -y -i "$CANON" -frames:v 1 -vf "$NORM" "$TMP/000_CANON.png"

i=0
shopt -s nullglob nocaseglob
for clip in "$SHOTS_DIR"/*.{mp4,mov,webm,mkv}; do
  i=$((i+1))
  name="$(basename "${clip%.*}")"
  printf 'sampling %s\n' "$name"
  # -ss before -i is a fast seek; fall back to frame 0 for very short clips.
  ffmpeg -loglevel error -ss "$GRAB_AT" -i "$clip" -frames:v 1 -vf "$NORM" \
         "$TMP/$(printf '%03d' "$i")_${name}.png" 2>/dev/null \
  || ffmpeg -loglevel error -i "$clip" -frames:v 1 -vf "$NORM" \
         "$TMP/$(printf '%03d' "$i")_${name}.png"
done

# Also accept still setup frames alongside clips. Re-encode rather than copy,
# so a mislabelled extension can't poison the montage.
for still in "$SHOTS_DIR"/*.{png,jpg,jpeg,webp}; do
  i=$((i+1))
  name="$(basename "${still%.*}")"
  printf 'reading %s\n' "$name"
  ffmpeg -loglevel error -y -i "$still" -frames:v 1 -vf "$NORM" \
         "$TMP/$(printf '%03d' "$i")_${name}.png"
done
shopt -u nullglob nocaseglob

count=$(find "$TMP" -type f | wc -l | tr -d ' ')
if [ "$count" -le 1 ]; then
  echo "no shots found in $SHOTS_DIR" >&2
  exit 1
fi

if command -v montage >/dev/null; then
  # ImageMagick: nicer output, keeps filename labels under each tile.
  montage "$TMP"/*.png \
    -label '%t' \
    -tile 5x \
    -geometry ${TILE}x+6+6 \
    -background '#111' -fill '#eee' -pointsize 13 \
    "$OUT"
else
  # ffmpeg-only fallback. No labels, but tiles read left-to-right in the
  # order printed above, with the canon frame first.
  echo "(ImageMagick not found — using ffmpeg tile, tiles are unlabelled)"
  cols=$(( count < 5 ? count : 5 ))
  rows=$(( (count + cols - 1) / cols ))
  # ffmpeg's tile filter emits nothing unless it receives exactly cols*rows
  # frames, so pad the set with black tiles to fill the final row.
  need=$(( cols * rows - count ))
  if [ "$need" -gt 0 ]; then
    ffmpeg -loglevel error -y -f lavfi -i "color=c=0x111111:s=${TILE}x${TILE}:d=1" \
           -frames:v 1 "$TMP/zzz_pad.png"
    for n in $(seq 1 "$need"); do cp "$TMP/zzz_pad.png" "$TMP/zzz_pad_$n.png"; done
    rm -f "$TMP/zzz_pad.png"
  fi
  ffmpeg -loglevel error -y -pattern_type glob -i "$TMP/*.png" \
    -filter_complex "tile=${cols}x${rows}:padding=6:color=0x111111" \
    -frames:v 1 "$OUT"
fi

echo "wrote $OUT  ($((count-1)) shots against canon)"
echo
echo "Check, in this order:"
echo "  1. face structure and proportion against the CANON tile, not against neighbours"
echo "  2. hair length, parting and colour"
echo "  3. marks: scars, tattoos, jewellery — present, right place, right size"
echo "  4. wardrobe: colour, fastenings, wear state"
echo "  5. apparent age — the most common slow drift, always younger"
