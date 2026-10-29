# Site BIG Solutions Management

Site static pentru bigsolutions.ro. Codul stă aici, în afara OneDrive.

- `src/data/` – datele: apelurile din calendar, paginile de program.
- `src/assets/` – stiluri, scripturi, fonturi, imagini.
- `tools/build.py` – generează site-ul în `dist/`.
- `tools/logo.swift` – generează fișierele logoului în `brand/` (SVG și PNG, cu textul transformat în contururi din fonturile site-ului): `swift tools/logo.swift brand`.
- `fise/` – fișele PDF oferite pe site (sursa HTML și PDF-ul): `sh fise/render.sh e-drive` reface `fise/e-drive.pdf` cu Chrome.

Construire: `python3 tools/build.py` (variante: `--test` pentru linkul de test, cu linkuri relative).
