# Site BIG Solutions Management

Site static pentru bigsolutions.ro. Codul stă aici, în afara OneDrive. La fiecare push pe `main`, GitHub Actions (`.github/workflows/publicare.yml`) construiește și publică site-ul pe GitHub Pages. Site-ul se reconstruiește automat și în fiecare noapte, la 22:05 UTC.

## Unde sunt lucrurile

- `src/data/`: datele.
  - `calls.json`: apelurile din calendar;
  - `pages.json`: paginile de program și de traseu;
  - `programs.json`, `featured.json`: lista programelor și apelurile alese pentru prima pagină. La fiecare program, `card` are rândurile fixe din cardul din dreapta al paginii (finanțator, cine aplică, finanțare). Starea și termenul din card vin din calendar;
  - `seo.json`: titlurile și descrierile pentru Google.
- `src/views/`, `src/partials/`: paginile și bucățile comune (antet, subsol, bara de pe telefon).
- `src/content/`: textele scrise în Markdown simplu (`## ` titluri, `- ` liste, `**îngroșat**`, `[text](adresă)`).
  - `legal/`: politica de confidențialitate, politica de cookies, termenii;
  - `apeluri/<slug>.md`: textul propriu al unei fișe de apel („Pentru cine merită”, „Unde se greșește des”, „Ce documente pregătiți”). Apare automat în fișa apelului cu același slug;
  - `noutati/AAAA-LL-ZZ-<slug>.md`: articolele din „Noutăți”. Antetul are rândurile `titlu:`, `data:`, `descriere:` și `apeluri:` (sluguri separate prin virgulă), apoi un rând `---` și textul.
- `src/assets/`: stiluri, scripturi, fonturi, imagini.
- `fise/`: fișele PDF oferite pe site, cu sursa HTML și PDF-ul. Le refaceți cu Chrome, cu `sh fise/render.sh <nume>`: `e-drive`, `autoritati`, `primarii-energie`. Toate PDF-urile din `fise/` ajung în `/assets/fise/`.
- `tools/build.py`: generează site-ul în `dist/`.
- `tools/imagini.py`: redimensionează imaginile și le salvează în JPEG și WebP, cu Chrome.
- `tools/logo.swift`: generează fișierele logoului în `brand/` (SVG și PNG, cu textul transformat în contururi din fonturile site-ului): `swift tools/logo.swift brand`.

## Construire

- `python3 tools/build.py`: varianta pentru bigsolutions.ro.
- `python3 tools/build.py --test`: varianta pentru linkul de test, cu linkuri relative, fără chei și fără statistici.
- Starea apelurilor (deschis sau închis) se calculează la construcție, după data zilei, iar `site.js` mai verifică o dată data în browser. Pentru încercări: `BIG_TODAY=2026-11-28 python3 tools/build.py --test`.
- Imaginile și PDF-urile primesc automat o versiune în adresă (`?v=<hash>`), deci un fișier înlocuit apare imediat. Fonturile nu primesc versiune, ca preîncărcarea să se potrivească cu CSS-ul.

## Cheile din `tools/build.py`

Sunt publice și se folosesc doar în varianta reală:

- `FORMS_KEY`: Web3Forms, formularele trimise pe e-mail;
- `ANALYTICS_TOKEN`: Cloudflare Web Analytics, vizite fără cookie-uri;
- `UMAMI_ID`: Umami Cloud, fără cookie-uri. Numără apăsările pe telefon, WhatsApp și e-mail (`data-umami-event`) și formularele trimise (evenimentul „Formular trimis”).

## Mentenanță

Sarcinile programate din aplicația Claude:

- **joi, la 9:00:** verifică sursele oficiale, actualizează calendarul și propune articole pentru Noutăți. Urcă doar după acordul lui Vladimir;
- **pe 1 ale lunii, la 9:00:** raportul de trafic și cereri.

Pentru modificările simple făcute direct pe GitHub, vedeți ghidul „SITE BIG - CUM ACTUALIZEZ SITE-UL.md” din OneDrive.

Nu se ating niciodată setările de e-mail ale domeniului (MX, SPF, DKIM, DMARC), care sunt la Hostinger.
