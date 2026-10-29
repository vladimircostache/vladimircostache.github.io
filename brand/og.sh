#!/bin/sh
# Reface imaginea pentru distribuire (og:image) din brand/og.html, cu Chrome.
set -e
cd "$(dirname "$0")"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --allow-file-access-from-files --virtual-time-budget=3000 --window-size=1200,630 \
  --screenshot="$PWD/../src/assets/img/og-big-solutions.png" "file://$PWD/og.html" >/dev/null 2>&1
echo "src/assets/img/og-big-solutions.png"
