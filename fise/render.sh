#!/bin/sh
# Reface fișele PDF din fise/*.html, cu data și termenele din calendar, și le salvează în fise/.
# Construirea site-ului (inclusiv cea de noapte) le generează oricum singură; acestea sunt rezerva pentru când nu există Chrome.
# Folosire: sh fise/render.sh
set -e
cd "$(dirname "$0")/.."
python3 tools/build.py --fise
