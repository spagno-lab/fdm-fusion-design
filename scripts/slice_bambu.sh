#!/usr/bin/env bash
# Headless Bambu Studio slice in an isolated work dir.
#
# Usage:
#   slice_bambu.sh -m machine.json -p process.json -f filament.json [-f filament2.json] \
#                  [-d DEST_DIR] [-x "extra cli flags"] INPUT.(3mf|stl)
#
# - Presets must be FLATTENED (see flatten_profile.py) — inherited presets fail.
# - Bambu Studio writes large temp files into its working dir, so it runs inside a
#   fresh mktemp dir; that dir is left in place (path printed) for inspection/cleanup.
# - Override the binary with BAMBU_STUDIO=/path/to/binary.
set -euo pipefail

MACHINE="" PROCESS="" FILAMENTS=() DEST="$(pwd)" EXTRA=""
while getopts "m:p:f:d:x:h" o; do
  case "$o" in
    m) MACHINE="$OPTARG" ;;
    p) PROCESS="$OPTARG" ;;
    f) FILAMENTS+=("$OPTARG") ;;
    d) DEST="$OPTARG" ;;
    x) EXTRA="$OPTARG" ;;
    *) sed -n '2,12p' "$0"; exit 1 ;;
  esac
done
shift $((OPTIND - 1))
INPUT="${1:-}"
[[ -n "$INPUT" && -n "$MACHINE" && -n "$PROCESS" && ${#FILAMENTS[@]} -gt 0 ]] || { sed -n '2,12p' "$0"; exit 1; }

abspath() { python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$1"; }
INPUT="$(abspath "$INPUT")"; MACHINE="$(abspath "$MACHINE")"; PROCESS="$(abspath "$PROCESS")"
DEST="$(abspath "$DEST")"
FIL_ARG=""
for f in "${FILAMENTS[@]}"; do FIL_ARG+="${FIL_ARG:+;}$(abspath "$f")"; done

BIN="${BAMBU_STUDIO:-}"
if [[ -z "$BIN" ]]; then
  for c in bambu-studio BambuStudio /Applications/BambuStudio.app/Contents/MacOS/BambuStudio; do
    if command -v "$c" >/dev/null 2>&1 || [[ -x "$c" ]]; then BIN="$c"; break; fi
  done
fi
[[ -n "$BIN" ]] || { echo "Bambu Studio binary not found; set BAMBU_STUDIO=..." >&2; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/bslice.XXXXXX")"
mkdir -p "$WORK/out" "$DEST"
NAME="$(basename "${INPUT%.*}").gcode.3mf"
echo "work dir: $WORK"

set +e
( cd "$WORK" && "$BIN" \
    --slice 0 \
    --load-settings "$MACHINE;$PROCESS" \
    --load-filaments "$FIL_ARG" \
    --allow-newer-file \
    --skip-useless-pick \
    --mstpp 600 \
    --outputdir "$WORK/out/" \
    --export-3mf "$NAME" \
    $EXTRA \
    "$INPUT" ) >"$WORK/slice.log" 2>&1
RC=$?
set -e

[[ -f "$WORK/out/result.json" ]] && { echo "--- result.json"; cat "$WORK/out/result.json"; echo; }
if [[ $RC -ne 0 || ! -f "$WORK/out/$NAME" ]]; then
  echo "slice FAILED (rc=$RC). Last log lines:" >&2
  tail -n 30 "$WORK/slice.log" >&2
  exit 3
fi
cp "$WORK/out/$NAME" "$DEST/$NAME"
echo "sliced: $DEST/$NAME"
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/inspect_3mf.py" "$DEST/$NAME" || true
echo "(temp files remain in $WORK — remove when no longer needed)"
