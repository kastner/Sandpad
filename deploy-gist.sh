#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_FILE="$SCRIPT_DIR/pitch-detective.html"

if [ ! -f "$HTML_FILE" ]; then
  echo "❌ pitch-detective.html not found next to this script"
  exit 1
fi

echo "🎵 Creating public gist for Pitch Detective..."

URL=$(gh gist create --public --filename "index.html" "$HTML_FILE" 2>&1)
GIST_ID=$(echo "$URL" | grep -o '[a-f0-9]\{32\}' | head -1)

if [ -z "$GIST_ID" ]; then
  echo "Gist created at: $URL"
  PREVIEW="https://htmlpreview.github.io/?url=${URL}/raw/index.html"
else
  RAW="https://gist.githubusercontent.com/$(gh api user --jq .login)/$GIST_ID/raw/index.html"
  PREVIEW="https://htmlpreview.github.io/?url=$RAW"
fi

echo ""
echo "✅ Done! Open this URL on your phone:"
echo ""
echo "  $PREVIEW"
echo ""

# Try to copy to clipboard if available
if command -v pbcopy &>/dev/null; then
  echo "$PREVIEW" | pbcopy
  echo "  (URL copied to clipboard)"
elif command -v xclip &>/dev/null; then
  echo "$PREVIEW" | xclip -selection clipboard
  echo "  (URL copied to clipboard)"
fi

# Try to open in browser
if command -v open &>/dev/null; then
  open "$PREVIEW"
elif command -v xdg-open &>/dev/null; then
  xdg-open "$PREVIEW"
fi
