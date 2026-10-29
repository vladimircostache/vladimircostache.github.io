#!/bin/sh
# Generează PDF-ul unei fișe din fise/<nume>.html, cu logoul din brand/ și fonturile site-ului.
# Folosire: sh fise/render.sh e-drive
set -e
cd "$(dirname "$0")"
python3 -c "import sys;s=open(sys.argv[1]+'.html',encoding='utf-8').read();l=open('../brand/logo-big-solutions.svg',encoding='utf-8').read().strip();open('.'+sys.argv[1]+'.tmp.html','w',encoding='utf-8').write(s.replace('{{LOGO}}',l))" "$1"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-pdf-header-footer \
  --allow-file-access-from-files --virtual-time-budget=4000 --print-to-pdf="$PWD/$1.pdf" "file://$PWD/.$1.tmp.html" >/dev/null 2>&1
rm -f ".$1.tmp.html"
echo "fise/$1.pdf"
