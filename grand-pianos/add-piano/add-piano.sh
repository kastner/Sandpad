#!/usr/bin/env bash
# add-piano.sh — find untracked piano HTML files and show metadata
# Usage: ./add-piano.sh [model-name-fragment]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIANO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd "$PIANO_DIR/.." && pwd)"

# Find untracked HTML files in grand-pianos/ (exclude index.html)
UNTRACKED=$(git -C "$REPO_DIR" ls-files --others --exclude-standard -- "grand-pianos/*.html" 2>/dev/null \
  | grep -v 'grand-pianos/index.html' || true)

if [ -z "$UNTRACKED" ]; then
  echo "No untracked HTML files found in grand-pianos/"
  exit 0
fi

# No argument — list all
if [ -z "${1:-}" ]; then
  echo "Untracked HTML files in grand-pianos/:"
  echo "$UNTRACKED"
  exit 0
fi

# Find best match
MATCH=$(echo "$UNTRACKED" | grep -i "$1" | head -1 || true)
if [ -z "$MATCH" ]; then
  echo "No match for '$1'. Untracked files:"
  echo "$UNTRACKED"
  exit 1
fi

FULL_PATH="$REPO_DIR/$MATCH"
FILENAME=$(basename "$FULL_PATH")

echo "File:     $FILENAME"
echo "Path:     $FULL_PATH"

# Creation date — macOS birthtime via stat
BIRTH=$(stat -f "%SB" -t "%Y-%m-%d" "$FULL_PATH" 2>/dev/null || true)
MTIME=$(stat -f "%Sm" -t "%Y-%m-%d" "$FULL_PATH" 2>/dev/null || true)

if [ -n "$BIRTH" ] && [ "$BIRTH" != "1970-01-01" ]; then
  echo "Created:  $BIRTH"
else
  echo "Modified: $MTIME  (birth time unavailable, using mtime)"
fi

echo "Size:     $(wc -c < "$FULL_PATH" | tr -d ' ') bytes"
echo "Lines:    $(wc -l < "$FULL_PATH" | tr -d ' ')"
