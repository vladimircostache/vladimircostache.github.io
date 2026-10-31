# Generează site-ul static BIG Solutions în dist/.
#   python3 tools/build.py          → adrese curate (/programe/…/), pentru bigsolutions.ro
#   python3 tools/build.py --test   → linkuri relative cu index.html, pentru linkul de test
#   python3 tools/build.py --fise   → doar fișele PDF, salvate în fise/ (rezerva folosită când nu există Chrome)
import datetime, hashlib, html, json, os, posixpath, re, shutil, subprocess, sys, unicodedata, pathlib
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DIST = ROOT / 'src', ROOT / 'dist'
TEST = '--test' in sys.argv
UPD = '30.10.2026'
SITE = 'https://bigsolutions.ro'
LEGAL_UPD = '30.10.2026'
# Cheia publică Web3Forms: cererile din formulare ajung pe vladimir.costache@bigsolutions.ro.
# Fără cheie (și pe linkul de test) formularele nu trimit nimic.
FORMS_KEY = '822211f9-55a8-4c8a-910e-6b5f5aa3724a'  # formularul „Formular Contact BSM SRL”, site bigsolutions.ro
# Cheia publică Cloudflare Web Analytics pentru bigsolutions.ro (statistici fără cookie-uri).
ANALYTICS_TOKEN = '3263195b4cba4ca798d994edc5b5f120'
# Umami Cloud (fără cookie-uri): numără formularele trimise și apăsările pe telefon, WhatsApp și e-mail.
# Codul site-ului („Website ID”) din contul Umami; cât timp e gol, scriptul nu se încarcă.
UMAMI_ID = '2e7890f2-d9a2-4fc4-8d71-a3872cebf317'  # site-ul „Big Solutions Management SRL”, bigsolutions.ro
UMAMI_EVT = {'tel:': 'Sunați', 'https://wa.me/': 'WhatsApp', 'mailto:': 'E-mail'}
PORTRAITS = {'vladimir.jpg': 'vladimir-costache', 'carmen.jpg': 'carmen-ciobanu'}
PHONE, PHONE_TEL, WA = '0742 225 222', '+40742225222', 'https://wa.me/40742225222'

def read(rel): return (SRC / rel).read_text(encoding='utf-8')
def data(name): return json.loads(read('data/%s.json' % name))
calls, pages, programs, featured, seo = data('calls'), data('pages'), data('programs'), data('featured'), data('seo')
# Noutăți: câte un fișier src/content/noutati/AAAA-LL-ZZ-<slug>.md, cu un antet „cheie: valoare”
# (titlu, data, descriere, apeluri = sluguri din calls.json), apoi un rând „---” și textul articolului.
def read_news():
    out = []
    for f in sorted((SRC / 'content' / 'noutati').glob('*.md'), reverse=True):
        head, body = f.read_text(encoding='utf-8').split('\n---\n', 1)
        n = dict(l.split(': ', 1) for l in head.strip().split('\n'))
        n.update(slug=f.stem[11:], body=body, calls=[s.strip() for s in n.get('apeluri', '').split(',') if s.strip()])
        out.append(n)
    return out
news = read_news()
# Starea apelurilor se recalculează la fiecare construcție (site-ul se reconstruiește în fiecare noapte):
# un apel al cărui termen a trecut devine „Închis”, oricum ar fi scris în calls.json.
# Pentru încercări se poate simula altă zi: BIG_TODAY=2026-11-28 python3 tools/build.py --test
TODAY = (datetime.date.fromisoformat(os.environ['BIG_TODAY']) if os.environ.get('BIG_TODAY')
         else datetime.datetime.now(ZoneInfo('Europe/Bucharest')).date())
def ddate(d): return datetime.date(*map(int, reversed(d.split('.')))) if d else None
for _c in calls:
    if _c['s'] != 'inchis' and _c['close'] and ddate(_c['close']) < TODAY:
        _c['s'], _c['when'] = 'inchis', ''
# Versiunea stilurilor și a scriptului se schimbă odată cu conținutul lor, ca browserele să nu păstreze varianta veche.
ASSET_V = hashlib.md5((read('assets/css/site.css') + read('assets/js/site.js')).encode('utf-8')).hexdigest()[:8]

BL = {'deschis': 'Deschis', 'urmeaza': 'Urmează', 'consultare': 'În consultare', 'inchis': 'Închis'}
WHO = {'F': 'Firme', 'O': 'ONG-uri', 'A': 'Autorități'}
TRACKS = {'F': ('Firme', '/firme/'), 'O': ('ONG-uri', '/ong-uri/'), 'A': ('Autorități publice', '/autoritati-publice/')}
TRACK_BY_NAME = {v[0]: (k, v[1]) for k, v in TRACKS.items()}
PRE = {'F': 'firma', 'O': 'ong', 'A': 'uat'}
# Sloganul firmei, adaptat pe paginile de traseu (prima pagină păstrează „Business, fără compromis.”).
SLOGANS = {'Firme': 'Business, fără compromis.', 'ONG-uri': 'Proiecte sociale, fără compromis.', 'Autorități publice': 'Investiții publice, fără compromis.'}
LEGAL = {'Politica de confidențialitate': '/politica-de-confidentialitate/', 'Politica de cookies': '/politica-cookies/', 'Termeni și condiții': '/termeni-si-conditii/'}
LEGAL_DESC = {
    'Politica de confidențialitate': 'Cum folosim datele trimise prin site: ce date, de ce, cui le transmitem, cât timp le păstrăm și ce drepturi aveți.',
    'Politica de cookies': 'Site-ul nu folosește cookie-uri de reclamă, de urmărire sau de statistică. Ce folosim în schimb și cum controlați cookie-urile.',
    'Termeni și condiții': 'Condițiile de folosire a site-ului: informațiile despre programe, verificarea eligibilității, drepturile de autor și litigiile.'}

# Fișa gratuită pentru primării: formularul apare pe paginile pentru autorități (trimiterea e în site.js, ca la e-DRIVE).
MAGNET_PRIMARII = ('<section class="magnet sm" id="fisa-primarii"><div><span class="lbl">Fișă gratuită pentru primării</span>'
    '<h2 style="margin-top:6px">Cum pregătește o primărie un proiect de energie</h2>'
    '<p>Pe 2 pagini: pașii în ordine, documentele de bază, ce cuprinde hotărârea consiliului local, cum se achiziționează consultanța și programele deschise acum.</p></div>'
    '<form class="mform" data-subject="Fișa pentru primării" novalidate><input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">'
    '<label for="p-email" style="font-weight:600">Adresa de e-mail</label><input type="email" id="p-email" placeholder="nume@primaria.ro" autocomplete="email">'
    '<button class="btn or" type="submit">Trimite-mi fișa</button>'
    '<small class="note">Folosim adresa doar ca să vă anunțăm când apare fișa actualizată. Detalii în <a href="@/politica-de-confidentialitate/" target="_blank" rel="noopener">Politica de confidențialitate</a>.</small>'
    '<span class="msg" aria-live="polite"></span>'
    '<a class="dl" href="@/assets/fise/primarii-energie.pdf" download hidden>Descarcă fișa pentru primării (PDF, 2 pagini)</a></form></section>')

def esc(s): return html.escape(s or '', quote=True)
def md(t):
    """Markdown simplu pentru paginile legale: ## titluri, liste cu „- ”, **îngroșat**, [text](adresă)."""
    def inl(s):
        s = esc(s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
        def link(m):
            ext = m.group(2).startswith('http')
            return '<a href="%s"%s>%s</a>' % (m.group(2), ' target="_blank" rel="noopener"' if ext else '', m.group(1))
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, s)
    out = []
    for block in re.split(r'\n\s*\n', t.strip()):
        lines = block.strip().split('\n')
        if lines[0].startswith('## '): out.append('</section><section><h2>%s</h2>' % inl(lines[0][3:]))
        elif all(l.startswith('- ') for l in lines): out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % inl(l[2:]) for l in lines))
        else: out.append('<p>%s</p>' % inl(' '.join(lines)))
    return ('<section>' + ''.join(out) + '</section>').replace('<section></section>', '')
def slugify(t):
    t = unicodedata.normalize('NFD', t.lower())
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')
def prog_path(name): return '/programe/%s/' % slugify(name)
def badge(s): return '<span class="bdg b-%s">%s</span>' % (s, BL[s])
def when(c):
    if c.get('when'): return c['when']
    if c['s'] == 'deschis': return 'termen ' + c['close']
    if c['s'] == 'urmeaza': return ('se deschide la ' + c['open']) if c['open'] else 'dată neanunțată'
    return 'închis la ' + c['close']
def dkey(d): return ''.join(reversed(d.split('.'))) if d else '99999999'
def dc(c):
    """Termenul unui apel deschis, pentru site.js: dacă trece și reconstruirea de noapte nu a rulat,
    browserul îl arată oricum ca „Închis” (și îl scoate de pe prima pagină)."""
    return ' data-close="%s"' % dkey(c['close']) if c['s'] == 'deschis' and c['close'] else ''
RANK = {'deschis': 0, 'urmeaza': 1, 'consultare': 2, 'inchis': 3}
def sort_calls(lst): return sorted(lst, key=lambda c: (RANK[c['s']], dkey(c['close'])))
def n_apel(n, sg, pl):
    r = n % 100
    return '%d %s' % (n, sg) if n == 1 else '%d %s%s' % (n, 'de ' if n >= 20 and (r == 0 or r >= 20) else '', pl)

# ---- linkurile machetei (data-go) devin adrese reale; „@” marchează adresele interne
def target(attrs):
    go = attrs.get('data-go'); p = attrs.get('data-p', '')
    if go == 'acasa': return '@/' + (('#' + attrs['data-to']) if attrs.get('data-to') else '')
    if go == 'program': return '@/programe/autoconsum-si-stocare/'
    if go == 'prog': return '@' + (TRACK_BY_NAME[p][1] if attrs.get('data-k') == 'track' else prog_path(p))
    if go == 'apeluri': return '@/apeluri/'
    if go == 'apel': return '@/apeluri/%s/' % attrs['data-slug']
    if go == 'eligibilitate': return '@/verifica-eligibilitatea/' + (('?tip=' + attrs['data-preset']) if attrs.get('data-preset') else '')
    if go == 'despre': return '@/despre-noi/'
    if go == 'proiecte': return '@/proiecte/'
    if go == 'noutati': return '@/noutati/'
    if go == 'contact': return '@/contact/'
    raise ValueError(go)
def route_links(h):
    def fix(m):
        raw = m.group(1)
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', raw))
        if 'data-go' not in attrs: return m.group(0)
        href = target(attrs)
        raw = re.sub(r'\s(?:data-go|data-p|data-k|data-to|data-slug|data-preset)="[^"]*"', '', raw)
        raw = re.sub(r'\shref="[^"]*"', '', raw)
        return '<a href="%s"%s>' % (href, raw)
    return re.sub(r'<a\b([^>]*)>', fix, h)
def legal_links(h):
    for txt, path in LEGAL.items():
        h = h.replace('<a href="#acasa" data-go="acasa">%s</a>' % txt, '<a href="@%s">%s</a>' % (path, txt))
    return h
def contact_links(h):
    h = h.replace('<span class="btn out">Sunați: %s</span>' % PHONE, '<a class="btn out" href="tel:%s">Sunați: %s</a>' % (PHONE_TEL, PHONE))
    h = h.replace('<span class="btn out">WhatsApp</span>', '<a class="btn out" href="%s" target="_blank" rel="noopener">WhatsApp</a>' % WA)
    h = h.replace('<li>%s</li>' % PHONE, '<li><a href="tel:%s">%s</a></li>' % (PHONE_TEL, PHONE))
    h = h.replace('<li>vladimir.costache@bigsolutions.ro</li>', '<li><a href="mailto:vladimir.costache@bigsolutions.ro">vladimir.costache@bigsolutions.ro</a></li>')
    h = h.replace('<p><b>%s</b>' % PHONE, '<p><a href="tel:%s"><b>%s</b></a>' % (PHONE_TEL, PHONE))
    h = h.replace('<dd>%s</dd>' % PHONE, '<dd><a href="tel:%s">%s</a></dd>' % (PHONE_TEL, PHONE))
    # cardul „Preferați să vorbim?” scris simplu în machete primește linkurile de telefon și WhatsApp
    h = h.replace('<div class="acard dark"><b>Preferați să vorbim?</b><p>%s · luni–vineri, 9:00–18:00.</p></div>' % PHONE, TALK)
    return h

_VQ = {}
def vq(path):
    """Versiunea unei imagini sau a unui PDF din assets (?v=…): după o înlocuire, browserul ia imediat fișierul nou."""
    f = DIST / path.lstrip('/')
    # doar imaginile și PDF-urile; fonturile se cer din CSS fără versiune, iar preîncărcarea trebuie să aibă aceeași adresă
    if not (path.startswith(('/assets/img/', '/assets/fise/')) and f.is_file()): return ''
    if path not in _VQ: _VQ[path] = '?v=' + hashlib.md5(f.read_bytes()).hexdigest()[:8]
    return _VQ[path]

def finalize(h, page_path):
    """Adresele „@/…” devin absolute (site) sau relative cu index.html (test)."""
    here = page_path.strip('/')
    def url(u):
        path, rest = re.match(r'([^?#]*)(.*)', u).groups()
        rest = rest or vq(path)
        if not TEST: return path + rest
        rel = posixpath.relpath(path.strip('/') or '.', here or '.')
        if path.endswith('/'): rel = 'index.html' if rel == '.' else rel + '/index.html'
        return rel + rest
    h = re.sub(r'srcset="([^"]*)"', lambda m: 'srcset="%s"' % re.sub(r'@(/\S+)', lambda u: url(u.group(1)), m.group(1)), h)
    return re.sub(r'(href|src)="@(/[^"]*)"', lambda m: '%s="%s"' % (m.group(1), url(m.group(2))), h)

# ---- bucăți generate din date (în machetă le genera scriptul)
def call_list(lst, empty):
    if not lst: return '<p class="empty">%s</p>' % esc(empty)
    out = []
    for c in lst:
        out.append('<div class="cl"%s><div class="meta">%s<span class="js-when">%s</span></div><a class="cl-t" href="@/apeluri/%s/">%s</a><span class="cl-m">%s · %s</span></div>'
                   % (dc(c), badge(c['s']), esc(when(c)), c['slug'], esc(c['n']), esc(c['prog'][-1]), esc(c['sum'])))
    return ''.join(out)
def by_slug(s): return next(c for c in calls if c['slug'] == s)

def layout(page_path, title, desc, body, scripts=''):
    body = fix_headings(strip_mock(body))
    # portretele echipei: WebP de 240 px, cu JPEG ca rezervă
    for short, name in PORTRAITS.items():
        body = re.sub(r'(<img class="pphoto") src="%s"([^>]*>)' % re.escape(short),
                      r'<picture><source type="image/webp" srcset="@/assets/img/%s.webp">\1 src="@/assets/img/%s.jpg"\2</picture>' % (name, name), body)
    header = route_links(read('partials/header.html'))
    footer = contact_links(route_links(legal_links(read('partials/footer.html'))))
    mbar = read('partials/mbar.html').replace('<a class="c1" href="#contact" data-go="contact">', '<a class="c1" href="tel:%s">' % PHONE_TEL)
    mbar = route_links(mbar.replace('<a class="c2" href="#contact" data-go="contact">', '<a class="c2" href="%s" target="_blank" rel="noopener">' % WA))
    canonical = SITE + page_path
    favicon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 56'%3E%3Crect x='0' y='26' width='12' height='26' rx='3' fill='%23F28C28'/%3E%3Crect x='17' y='14' width='12' height='38' rx='3' fill='%23F28C28'/%3E%3Crect x='34' y='2' width='12' height='50' rx='3' fill='%23F28C28'/%3E%3C/svg%3E"
    doc = ('<!doctype html>\n<html lang="ro">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           '<title>%s</title>\n<meta name="description" content="%s">\n%s<link rel="canonical" href="%s">\n'
           '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n<meta property="og:type" content="website">\n<meta property="og:locale" content="ro_RO">\n'
           '<meta property="og:url" content="%s">\n<meta property="og:site_name" content="BIG Solutions Management">\n'
           '<meta property="og:image" content="%s/assets/img/og-big-solutions.png">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
           '<meta name="twitter:card" content="summary_large_image">\n'
           '<link rel="icon" href="%s">\n<link rel="apple-touch-icon" href="@/assets/img/apple-touch-icon.png">\n<link rel="preload" href="@/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>\n<link rel="preload" href="@/assets/fonts/bricolage-grotesque-latin-ext.woff2" as="font" type="font/woff2" crossorigin>\n'
           '<link rel="stylesheet" href="@/assets/css/site.css?v=' + ASSET_V + '">\n%s</head>\n<body>\n<div class="site" id="site">\n%s\n<main id="main">\n%s\n</main>\n%s\n%s\n</div>\n%s<script src="@/assets/js/site.js?v=' + ASSET_V + '" defer></script>\n</body>\n</html>\n') % (
        esc(title), esc(desc), '<meta name="robots" content="noindex">\n' if TEST else '', canonical, esc(title), esc(desc), canonical, SITE, favicon,
        JSONLD if page_path == '/' else '',
        header, body, footer, mbar, scripts)
    fk = '' if TEST else FORMS_KEY
    # Statistici fără cookie-uri (Cloudflare Web Analytics), doar pe bigsolutions.ro, nu pe linkul de test.
    if not TEST and ANALYTICS_TOKEN:
        doc = doc.replace('</body>', '<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{"token": "%s"}\'></script>\n</body>' % ANALYTICS_TOKEN, 1)
    if not TEST and UMAMI_ID:
        doc = doc.replace('</body>', '<script defer src="https://cloud.umami.is/script.js" data-website-id="%s"></script>\n</body>' % UMAMI_ID, 1)
    doc = contact_links(route_links(doc)).replace('<body>', '<body data-ix="%s"%s>' % ('index.html' if TEST else '', ' data-fk="%s"' % fk if fk else ''), 1)
    doc = re.sub(r'<a\b([^>]*?) href="(tel:|https://wa\.me/|mailto:)', lambda m: '<a%s data-umami-event="%s" href="%s' % (m.group(1), UMAMI_EVT[m.group(2)], m.group(2)), doc)
    return finalize(doc, '/' if page_path == '/404/' else page_path)

# Datele firmei, în formatul citit de Google (doar pe prima pagină). Adresa biroului se adaugă când o primim.
JSONLD = '<script type="application/ld+json">%s</script>\n' % json.dumps({
    '@context': 'https://schema.org', '@type': 'ProfessionalService',
    'name': 'BIG Solutions Management', 'legalName': 'Big Solutions Management SRL', 'taxID': '45692645',
    'url': SITE + '/', 'logo': SITE + '/assets/img/logo-big-solutions.png', 'image': SITE + '/assets/img/og-big-solutions.png',
    'description': 'Consultanță pentru fonduri nerambursabile: energie, echipamente și inovație, pentru firme, ONG-uri și autorități publice.',
    'telephone': '+40742225222', 'email': 'vladimir.costache@bigsolutions.ro', 'areaServed': 'RO',
    'address': {'@type': 'PostalAddress', 'streetAddress': 'Ale. Petre Antonescu nr. 1', 'addressLocality': 'București', 'addressCountry': 'RO'},
    'openingHours': 'Mo-Fr 09:00-18:00'}, ensure_ascii=False)

def fix_headings(h):
    """Titlurile din pagină nu sar niveluri (h2 → h4), pentru cititoarele de ecran.
    Un titlu coborât păstrează aspectul vechi prin clasa „hN”."""
    stack = [(1, 1)]  # (nivelul scris, nivelul corectat) al titlurilor părinte
    def one(m):
        lvl, attrs, inner = int(m.group(1)), m.group(2), m.group(3)
        while stack and stack[-1][0] >= lvl: stack.pop()
        new = min(lvl, (stack[-1][1] if stack else 0) + 1)
        stack.append((lvl, new))
        if new == lvl: return m.group(0)
        if 'class="' in attrs: attrs = attrs.replace('class="', 'class="h%d ' % lvl, 1)
        else: attrs += ' class="h%d"' % lvl
        return '<h%d%s>%s</h%d>' % (new, attrs, inner, new)
    return re.sub(r'<h([1-6])((?:\s[^>]*)?)>(.*?)</h\1>', one, h, flags=re.S)

def write_page(page_path, title, desc, body, scripts=''):
    out = DIST / page_path.strip('/') / 'index.html' if page_path != '/404/' else DIST / '404.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(layout(page_path, title, desc, body, scripts), encoding='utf-8')
    return out

def strip_mock(h):
    h = re.sub(r'\s*<p class="mocknote"[^>]*>.*?</p>', '', h, flags=re.S)
    return h

# ---- prima pagină
def build_home():
    v = read('views/acasa.html')
    # „Ce puteți depune acum”: o bandă derulabilă cu apelurile deschise. Întâi cele alese în featured.json,
    # apoi celelalte, după termen; apelurile închise dispar singure (starea e calculată după dată).
    shown = [c for c in map(by_slug, featured) if c['s'] == 'deschis']
    shown += sorted((c for c in calls if c['s'] == 'deschis' and c['pg'] and c not in shown), key=lambda c: dkey(c['close']))
    shown = shown[:12]
    feat = ''
    for c in shown:
        feat += ('<div class="call"%s><div class="meta">%s<span>%s</span></div><h4>%s</h4><span class="who">%s</span><span class="sum">%s</span>'
                 '<a class="link" href="@%s">Pagina programului&nbsp;→</a></div>') % (dc(c), badge(c['s']), esc(when(c)), esc(c['n']), esc(c['prog'][-1]), esc(c['sum']), prog_path(c['pg']))
    v = re.sub(r'(<div class="calls[^"]*" id="featured"[^>]*>)(</div>)', lambda m: m.group(1) + feat + m.group(2), v, count=1)
    # banda arată o selecție; butonul spune câte apeluri deschise sunt în total, ca cifrele să nu se contrazică
    n_all = sum(1 for c in calls if c['s'] == 'deschis')
    v = v.replace('>Vedeți calendarul complet\u00a0→</a>', '>Toate cele %s\u00a0→</a>' % n_apel(n_all, 'apel deschis', 'apeluri deschise'), 1)
    # „Unde vă putem ajuta”: liste scurte de linkuri pe tip de solicitant, cu numărul de apeluri deschise
    groups = ''
    for f, title in [('F', 'Pentru firme'), ('O', 'Pentru ONG-uri'), ('A', 'Pentru autorități publice')]:
        items = ''
        for p in (p for p in programs if f in p['t']):
            # se numără doar apelurile pentru acest tip de solicitant (la Incluziune socială, ONG-urile au 7 din 8)
            mine = [c for c in calls if c['pg'] == p['n'] and f in c['w']]
            n_open = sum(1 for c in mine if c['s'] == 'deschis')
            note = n_apel(n_open, 'apel deschis', 'apeluri deschise') if n_open else ('urmează' if any(c['s'] == 'urmeaza' for c in mine) else 'niciun apel acum')
            items += '<li><a href="@%s"><span>%s</span><span class="pc%s">%s</span></a></li>' % (prog_path(p['n']), esc(p['n']), ' on' if n_open else '', note)
        extra = ''
        if f == 'O':
            # ONG-urile au un singur program: dedesubt, apelurile deschise pentru ele, cu termenul
            lst = sorted((c for c in calls if c['s'] == 'deschis' and 'O' in c['w']), key=lambda c: dkey(c['close']))
            extra = ''.join('<li%s><a href="@/apeluri/%s/"><span>%s</span><span class="pc">%s</span></a></li>'
                            % (dc(c), c['slug'], esc(c['n']), esc('până la ' + c['close'][:5] if c['close'] else when(c))) for c in lst[:5])
            if extra:
                more = '<a class="link pl-more" href="@/apeluri/?solicitant=ong&amp;stare=deschis">Toate cele %s pentru ONG-uri →</a>' % n_apel(len(lst), 'apel', 'apeluri') if len(lst) > 5 else ''
                extra = '<p class="pl-sub">Apeluri deschise acum</p><ul class="pl-calls">%s</ul>%s' % (extra, more)
        groups += '<div class="pl"><h3>%s</h3><ul>%s</ul>%s</div>' % (title, items, extra)
    v = v.replace('<div class="plinks" id="plinks"></div>', '<div class="plinks" id="plinks">%s</div>' % groups)
    # ultimele articole din Noutăți, ca să se vadă că site-ul e ținut la zi; fără articole, secțiunea dispare
    if news:
        v = v.replace('<div class="newsgrid" id="home-news"></div>', '<div class="newsgrid" id="home-news">%s</div>' % ''.join(
            '<article class="news"><span class="nd">%s</span><h3><a href="@/noutati/%s/">%s</a></h3><p>%s</p></article>'
            % (esc(n['data']), n['slug'], esc(n['titlu']), esc(n['descriere'])) for n in news[:3]))
    else:
        v = re.sub(r'\s*<section class="sec" id="noutati-acasa">.*?</section>', '', v, flags=re.S)
    s = seo['/']
    write_page('/', s['title'], s['description'], strip_mock(v))

# ---- starea unui program și cardul din dreapta: starea și termenul vin din calendar, restul din programs.json („card”)
def prog_badge(lst):
    n = sum(1 for c in lst if c['s'] == 'deschis')
    return ('<span class="bdg b-deschis">%s</span>' % n_apel(n, 'apel deschis', 'apeluri deschise')) if n else '<span class="bdg b-inchis">Niciun apel deschis acum</span>'
def prog_close(lst):
    """Termenul comun al apelurilor deschise, pentru site.js; gol dacă au termene diferite sau nu au termen."""
    op = [c for c in lst if c['s'] == 'deschis']
    return dc(op[0]) if op and all(c['close'] for c in op) and len({c['close'] for c in op}) == 1 else ''
# cardul închis la culoare din dreapta, același pe toate paginile cu cadrul Autoconsum
TALK = ('<div class="acard dark"><b>Preferați să vorbim?</b><p><a href="tel:%s">%s</a> · luni–vineri, 9:00–18:00. Sau scrieți-ne pe '
        '<a href="%s" target="_blank" rel="noopener">WhatsApp</a>.</p></div>' % (PHONE_TEL, PHONE, WA))
def prog_side(card, lst, preset):
    op = [c for c in lst if c['s'] == 'deschis']
    nx = [c for c in lst if c['s'] != 'deschis']
    dated = sorted((c for c in op if c['close']), key=lambda c: dkey(c['close']))
    if prog_close(lst): row = ['Termen', op[0]['close']]
    elif dated: row = ['Primul termen', dated[0]['close']]
    elif op: row = ['Perioada', when(op[0])]
    elif nx: row = ['Urmează', when(nx[0]) if len(nx) == 1 else n_apel(len(nx), 'apel în pregătire', 'apeluri în pregătire')]
    else: row = ['Sesiune', 'niciuna anunțată acum']
    dl = ''.join('<div><dt>%s</dt><dd%s>%s</dd></div>' % (a, ' class="js-when"' if i == 0 and prog_close(lst) else '', esc(b)) for i, (a, b) in enumerate([row] + card))
    return ('<aside class="aside"><div class="acard sum"%s>%s<dl>%s</dl><a class="btn or" href="#eligibilitate" data-go="eligibilitate" data-preset="%s">Verifică eligibilitatea</a></div>%s</aside>'
            % (prog_close(lst), prog_badge(lst), dl, preset, TALK))

# ---- pagina Autoconsum (scrisă integral în machetă; starea și cardul din dreapta vin din calendar)
def build_autoconsum():
    v = read('views/program.html')
    name = 'Autoconsum și stocare'
    lst = sort_calls([c for c in calls if c['pg'] == name and c['s'] != 'inchis'])
    v = v.replace('<div class="st" id="pr-st"></div>', '<div class="st" id="pr-st"%s>%s<span>Actualizat la %s</span></div>' % (prog_close(lst), prog_badge(lst), UPD))
    v = v.replace('<aside class="aside" id="pr-side"></aside>', prog_side(next(p for p in programs if p['n'] == name)['card'], lst, 'uat'))
    v = v.replace('<div class="cls" id="pr-calls"></div>', '<div class="cls" id="pr-calls">%s</div>' % call_list(lst, 'Nu sunt apeluri deschise acum.'))
    a = '<section>\n            <h2>Apelurile deschise acum</h2>'
    assert a in v
    v = v.replace(a, MAGNET_PRIMARII + a, 1)
    s = seo['/programe/autoconsum-si-stocare/']
    write_page('/programe/autoconsum-si-stocare/', s['title'], s['description'], strip_mock(v))

# ---- paginile de program și de traseu, pe cadrul paginii Autoconsum: textul în stânga, cardul cu termenul în dreapta.
# Rândurile fixe ale cardului: programs.json („card”) la programe, pages.json („card”) la Firme, ONG-uri și Autorități publice.
def build_prog(name, track=None):
    v = read('views/prog.html')
    key = ('traseu:' + name) if track else name
    pg = pages[key]
    if track:
        f, path = TRACK_BY_NAME[name]
        lst = sort_calls([c for c in calls if c['s'] == 'deschis' and f in c['w'] and c['pg']])
        crumb = '<span>%s</span>' % esc(name)
        heading, preset, card = 'Apelurile deschise acum', PRE[f], pg['card']
    else:
        pr = next(p for p in programs if p['n'] == name)
        f = pr['t'][0]; path = prog_path(name)
        lst = sort_calls([c for c in calls if c['pg'] == name and c['s'] != 'inchis'])
        tname, tpath = TRACKS[f]
        crumb = '<a href="@%s">%s</a><span>/</span><span>%s</span>' % (tpath, esc(tname), esc(name))
        heading, preset, card = 'Apelurile deschise și cele care urmează', pg.get('pre', PRE[f]), pr['card']
    body = pg['h'].replace('class="btn ink prep-elig" href="#eligibilitate" data-go="eligibilitate"', 'class="btn ink prep-elig" href="#eligibilitate" data-go="eligibilitate" data-preset="%s"' % preset)
    if name in ('Autorități publice', 'Eficiență energetică pentru clădiri publice'): body += MAGNET_PRIMARII
    rep = {'<span id="pg-cr"></span>': crumb,
           '<div class="st" id="pg-st"></div>': '<div class="st"%s>%s<span>Actualizat la %s</span></div>' % (prog_close(lst), prog_badge(lst), UPD),
           '<h1 id="pg-t"></h1>': '%s<h1 id="pg-t">%s</h1>' % ('<span class="slog">%s</span>' % SLOGANS[name] if track else '', esc(pg['t'])),
           '<p class="lead" id="pg-l"></p>': '<p class="lead" id="pg-l">%s</p>' % esc(pg['l']),
           '<div id="pg-body"></div>': body,
           'id="pg-ch">Apelurile deschise și cele care urmează<': 'id="pg-ch">%s<' % heading,
           '<div class="cls" id="pg-calls"></div>': '<div class="cls" id="pg-calls">%s</div>' % call_list(lst, 'Nu sunt apeluri deschise acum. Când apare unul, îl vedeți aici și în calendar.'),
           'data-go="eligibilitate" id="pg-elig"': 'data-go="eligibilitate" data-preset="%s" id="pg-elig"' % preset,
           '<aside class="aside" id="pg-side"></aside>': prog_side(card, lst, preset)}
    for a, b in rep.items():
        assert a in v, a
        v = v.replace(a, b)
    s = seo[path]
    write_page(path, s['title'], s['description'], v)

# ---- fișa fiecărui apel
def build_call(c):
    v = read('views/apel.html')
    st = badge(c['s']) + '<span class="js-when">%s</span><span>Actualizat la %s</span>' % (esc(when(c)), UPD)
    # Tipul apelului are doar 3 variante (calls.json). Unde sursa nu-l spune, arătăm ce știm despre ghid, nu „conform ghidului”.
    if c.get('tip'): tip = [[c['tip'], 'tipul apelului']]
    elif c.get('ghid'): tip = [[c['ghid'], 'data ghidului solicitantului']]
    elif c['s'] == 'urmeaza' and not c.get('extra') and 'ghid' not in when(c): tip = [['nepublicat încă', 'ghidul solicitantului']]
    else: tip = []
    facts = [[(c['open'] + ' – ' + c['close']) if c['open'] and c['close'] else when(c), 'perioada de depunere'], [c['sum'], 'buget'], [BL[c['s']], 'starea apelului']] + tip + (c.get('extra') or [])
    fh = ''.join('<div><b%s>%s</b><span>%s</span></div>' % (' class="js-st"' if b == 'starea apelului' else '', esc(a), esc(b)) for a, b in facts)
    ben = ''.join('<span class="tag">%s</span>' % esc(x) for x in c['ben']) or '<span>Categoriile exacte sunt în ghidul oficial.</span>'
    if c.get('pg'):
        pgl = '<a class="link" href="@%s">Pagina programului: %s&nbsp;→</a>' % (prog_path(c['pg']), esc(c['pg']))
    else:
        pgl = 'Pentru acest program nu avem o pagină dedicată. Vă putem ajuta oricum: verificați eligibilitatea sau sunați-ne.'
    dl = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (a, esc(b)) for a, b in [['Termen', c['close'] if c['s'] == 'deschis' and c['close'] else when(c)], ['Buget', c['sum']], ['Program', c['prog'][-1]]])
    src = 'Sursa: %s · actualizat la %s' % (c.get('srcname') or ('oportunitati-ue.gov.ro' if c.get('url') else c.get('src', '')), UPD)
    rep = {'<span id="ap-cr"></span>': '<span id="ap-cr">%s</span>' % esc(c['n']),
           '<div class="st" id="ap-st"></div>': '<div class="st" id="ap-st">%s</div>' % st,
           '<h1 id="ap-t"></h1>': '<h1 id="ap-t">%s</h1>' % esc(c['n']),
           '<p class="lead" id="ap-l"></p>': '<p class="lead" id="ap-l">%s</p>' % esc(c['rez']),
           '<div class="facts4" id="ap-f"></div>': '<div class="facts4" id="ap-f">%s</div>' % fh,
           '<div class="chipsx" id="ap-b"></div>': '<div class="chipsx" id="ap-b">%s</div>' % ben,
           '<p id="ap-p"></p>': '<p id="ap-p">%s</p>' % esc(' · '.join(c['prog'])),
           '<p id="ap-pg"></p>': '<p id="ap-pg">%s</p>' % pgl,
           'id="ap-full"></p>': 'id="ap-full">%s</p>' % (esc(c['full']) + ('<br><small>Cod: %s</small>' % esc(c['cod']) if c.get('cod') else '')),
           '<span id="ap-badge" style="justify-self:start"></span>': '<span id="ap-badge" style="justify-self:start">%s</span>' % badge(c['s']),
           '<dl id="ap-dl"></dl>': '<dl id="ap-dl">%s</dl>' % dl,
           'data-go="eligibilitate" id="ap-elig"': 'data-go="eligibilitate" data-preset="%s" id="ap-elig"' % PRE[c['w'][-1]],
           '<small id="ap-src" style="color:var(--mut)"></small>': '<small id="ap-src" style="color:var(--mut)">%s</small>' % esc(src)}
    for a, b in rep.items():
        assert a in v, a
        v = v.replace(a, b)
    v = v.replace('<a class="link" id="ap-off" href="#"', '<a class="link" id="ap-off" href="%s"' % esc(c['url'])) if c.get('url') else re.sub(r'\s*<a class="link" id="ap-off"[^>]*>[^<]*</a>', '', v)
    if c.get('url2'):
        v = v.replace('<a class="link" id="ap-off2" href="#" target="_blank" rel="noopener" hidden></a>', '<a class="link" id="ap-off2" href="%s" target="_blank" rel="noopener">%s ↗</a>' % (esc(c['url2']), esc(c['label2'])))
    else:
        v = re.sub(r'\s*<a class="link" id="ap-off2"[^>]*></a>', '', v)
    title = '%s | BIG Solutions' % c['n']
    desc = c['rez'] if len(c['rez']) <= 160 else c['rez'][:157].rsplit(' ', 1)[0] + '…'
    # text propriu (pentru cine merită, unde se greșește, ce documente), scris în src/content/apeluri/<slug>.md
    own = SRC / 'content' / 'apeluri' / (c['slug'] + '.md')
    if own.exists():
        v = v.replace('<section><h2>Cine poate aplica</h2>', '<div class="own">%s</div><section><h2>Cine poate aplica</h2>' % md(own.read_text(encoding='utf-8')), 1)
    rel = [n for n in news if c['slug'] in n['calls']]
    if rel:
        v = v.replace('<div class="acard dark">', '<div class="acard"><b>Noutăți despre acest apel</b>%s</div><div class="acard dark">'
                      % ''.join('<a class="link" href="@/noutati/%s/">%s&nbsp;→</a>' % (n['slug'], esc(n['titlu'])) for n in rel), 1)
    if dc(c): v = '<div class="cwrap"%s>%s</div>' % (dc(c), v)
    write_page('/apeluri/%s/' % c['slug'], title, desc, strip_mock(v))

# ---- calendar, eligibilitate, despre, contact, pagini legale (în lucru), 404
# ---- Noutăți: lista și pagina fiecărui articol
def build_news():
    items = ''.join('<article class="news"><span class="nd">%s</span><h2><a href="@/noutati/%s/">%s</a></h2><p>%s</p></article>'
                    % (esc(n['data']), n['slug'], esc(n['titlu']), esc(n['descriere'])) for n in news)
    body = ('<section class="phead"><div class="wrap"><nav class="crumbs" aria-label="Unde vă aflați"><a href="@/">Prima pagină</a><span>/</span><span>Noutăți</span></nav>'
            '<h1>Noutăți</h1><p class="lead">Lansări, prelungiri și schimbări importante la apelurile din programele pe care lucrăm, explicate pe scurt. '
            'Calendarul complet e în <a class="link" href="@/apeluri/">Calendar apeluri</a>.</p></div></section>'
            '<div class="wrap pgrid"><div class="pmain"><div class="newslist">%s</div></div><aside class="aside">'
            '<div class="acard">%s<dl><div><dt>Calendarul</dt><dd>actualizat la %s</dd></div></dl>'
            '<a class="btn or" href="@/verifica-eligibilitatea/">Verifică eligibilitatea</a><a class="link" href="@/apeluri/">Calendar apeluri&nbsp;→</a></div>%s</aside></div>') % (
        items or '<p class="empty">Primele articole apar în curând.</p>', prog_badge(calls), UPD, TALK)
    write_page('/noutati/', 'Noutăți despre fonduri nerambursabile | BIG Solutions',
               'Lansări, prelungiri și schimbări la apelurile de finanțare pentru firme, ONG-uri și autorități publice, explicate pe scurt de BIG Solutions.', body)
    for n in news:
        rel = [c for c in calls if c['slug'] in n['calls']]
        aside = ('<div class="acard"><b>Apelurile din articol</b><div class="cls">%s</div><a class="btn or" href="@/verifica-eligibilitatea/">Verifică eligibilitatea</a></div>' % call_list(rel, '')) if rel else ''
        body = ('<section class="phead"><div class="wrap"><nav class="crumbs" aria-label="Unde vă aflați"><a href="@/">Prima pagină</a><span>/</span><a href="@/noutati/">Noutăți</a></nav>'
                '<div class="st"><span>Publicat pe %s</span></div><h1>%s</h1><p class="lead">%s</p></div></section>'
                '<div class="wrap pgrid"><div class="pmain">%s</div><aside class="aside">%s%s</aside></div>') % (
            esc(n['data']), esc(n['titlu']), esc(n['descriere']), md(n['body']), aside, TALK)
        ld = '<script type="application/ld+json">%s</script>\n' % json.dumps({
            '@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': n['titlu'], 'description': n['descriere'],
            'datePublished': '-'.join(reversed(n['data'].split('.'))), 'inLanguage': 'ro',
            'author': {'@type': 'Organization', 'name': 'BIG Solutions Management'},
            'publisher': {'@type': 'Organization', 'name': 'BIG Solutions Management', 'logo': {'@type': 'ImageObject', 'url': SITE + '/assets/img/logo-big-solutions.png'}},
            'mainEntityOfPage': SITE + '/noutati/%s/' % n['slug']}, ensure_ascii=False)
        write_page('/noutati/%s/' % n['slug'], '%s | BIG Solutions' % n['titlu'], n['descriere'], body, ld)

def build_rest():
    keep = ['n', 'prog', 'w', 's', 'open', 'close', 'when', 'sum', 'slug']
    def plain(t): return ''.join(ch for ch in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(ch) != 'Mn')
    rows = [dict({k: c.get(k) for k in keep}, q=plain(' '.join([c['n'], ' '.join(c['prog']), c.get('full', ''), c.get('cod', ''), c.get('rez', ''), ' '.join(c.get('ben') or [])]))) for c in calls]
    data_js = '<script>window.CALLS=%s;</script>\n' % json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    write_page('/apeluri/', 'Calendar apeluri de finanțare | BIG Solutions',
               'Apelurile deschise și cele care urmează din programele pe care lucrăm: cine poate aplica, termenul și bugetul. Actualizat săptămânal.',
               read('views/apeluri.html'), data_js)
    write_page('/verifica-eligibilitatea/', 'Verifică eligibilitatea | BIG Solutions',
               'În 4 pași aflați dacă proiectul dumneavoastră poate primi finanțare. Discuția de principiu e gratuită.', read('views/eligibilitate.html'))
    for path, view in [('/despre-noi/', 'despre'), ('/contact/', 'contact'), ('/proiecte/', 'proiecte')]:
        v = read('views/%s.html' % view)
        v = v.replace('<div class="st"><span class="bdg b-consultare">Text de aprobat</span><span>Scris în Etapa 5</span></div>\n', '')
        write_page(path, seo[path]['title'], seo[path]['description'], v)
    for name, path in LEGAL.items():
        body = ('<section class="phead"><div class="wrap"><nav class="crumbs" aria-label="Unde vă aflați"><a href="@/">Prima pagină</a><span>/</span><span>%s</span></nav>'
                '<h1>%s</h1><p class="lead">Ultima actualizare: %s.</p></div></section>'
                '<section class="sec"><div class="wrap pmain legal">%s</div></section>') % (name, name, LEGAL_UPD, md(read('content/legal/%s.md' % path.strip('/'))))
        write_page(path, '%s | BIG Solutions' % name, LEGAL_DESC[name], body)
    write_page('/404/', 'Pagina nu există | BIG Solutions', 'Pagina căutată nu există.',
               '<section class="phead"><div class="wrap"><h1>Pagina nu există</h1><p class="lead">Adresa nu mai e valabilă sau a fost scrisă greșit.</p>'
               '<div class="ctas" style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap"><a class="btn or" href="@/">Prima pagină</a><a class="btn out" href="@/apeluri/">Calendar apeluri</a></div></div></section>')

# ---- fișele PDF: se generează din fise/<nume>.html la fiecare construire, deci și în cea de noapte, cu Chrome.
# Data („Situația la”) e UPD; tabelul cu data-calendar își ia apelurile și termenele din calendar, iar un text
# cu data-stare="<slug>" rămâne doar cât timp apelul urmează. Fără Chrome se folosesc PDF-urile salvate în fise/.
FISE = ['e-drive', 'autoritati', 'primarii-energie']
FISE_PROG = ['Autoconsum și stocare', 'Eficiență energetică pentru clădiri publice', 'Iluminat public']
def chrome():
    for c in (os.environ.get('CHROME'), shutil.which('google-chrome'), shutil.which('google-chrome-stable'), shutil.which('chromium'),
              '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        if c and os.path.exists(c): return c
def fisa_html(name):
    h = (ROOT / 'fise' / (name + '.html')).read_text(encoding='utf-8')
    h = h.replace('{{LOGO}}', (ROOT / 'brand' / 'logo-big-solutions.svg').read_text(encoding='utf-8').strip()).replace('{{UPD}}', UPD)
    def stare(m):
        c = by_slug(m.group(1))
        if c['s'] == 'deschis': return 'Apelul e deschis%s. Detalii: bigsolutions.ro/apeluri/%s/' % (', cu termen pe ' + c['close'] if c['close'] else '', c['slug'])
        if c['s'] == 'inchis': return 'Apelul s-a închis. Calendarul actualizat: bigsolutions.ro/apeluri'
        return m.group(2)
    h = re.sub(r'<span data-stare="([^"]+)">(.*?)</span>', lambda m: '<span>%s</span>' % stare(m), h)
    def table(m):
        # rândurile scrise în fișă dau doar textele (programul și ce finanțează); apelurile deschise sau care urmează și termenele vin din calendar
        own = {s: (a, b) for s, a, b in re.findall(r'<tr data-slug="([^"]+)"><td>(.*?)</td><td>(.*?)</td>', m.group(1))}
        lst = [c for p in FISE_PROG for c in sort_calls([c for c in calls if c['pg'] == p and 'A' in c['w'] and c['s'] != 'inchis'])]
        def term(c): return ('d', c['close']) if c['s'] == 'deschis' and c['close'] else ('d lung', esc(when(c)))
        rows = ''.join('<tr><td>%s</td><td>%s</td><td class="%s">%s</td></tr>' % (own.get(c['slug'], (esc(c['prog'][-1]), esc(c['n']))) + term(c)) for c in lst)
        return '<tbody>%s</tbody>' % (rows or '<tr><td colspan="3">Niciun apel deschis acum. Calendarul actualizat: bigsolutions.ro/apeluri</td></tr>')
    return re.sub(r'<tbody data-calendar>(.*?)</tbody>', table, h, flags=re.S)
def render_fise(out):
    ch = chrome()
    linux = ['--no-sandbox', '--disable-dev-shm-usage'] if sys.platform.startswith('linux') else []
    for name in FISE:
        pdf, ok = out / (name + '.pdf'), False
        if ch:
            tmp = ROOT / 'fise' / ('.%s.tmp.html' % name)
            tmp.write_text(fisa_html(name), encoding='utf-8')
            try:
                subprocess.run([ch, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files', '--virtual-time-budget=4000']
                               + linux + ['--print-to-pdf=%s' % pdf, tmp.as_uri()], capture_output=True, timeout=180)
            except subprocess.TimeoutExpired: pass
            tmp.unlink()
            b = pdf.read_bytes() if pdf.exists() else b''
            ok = b[:4] == b'%PDF' and len(b) > 20000
            if ok and b'/Count 2' not in b: print('Atenție: fișa %s nu mai are 2 pagini; verificați textul din fise/%s.html.' % (name, name))
        if not ok:
            print('Atenție: fișa %s nu s-a putut genera; rămâne PDF-ul salvat în fise/.' % name)
            if out != ROOT / 'fise': shutil.copy(ROOT / 'fise' / (name + '.pdf'), pdf)

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(SRC / 'assets', DIST / 'assets')
    (DIST / 'assets' / 'fise').mkdir(exist_ok=True)
    render_fise(DIST / 'assets' / 'fise')
    build_home(); build_autoconsum()
    for p in programs:
        if p['n'] != 'Autoconsum și stocare': build_prog(p['n'])
    for t in TRACK_BY_NAME: build_prog(t, track=True)
    for c in calls: build_call(c)
    build_news(); build_rest()
    pages_all = sorted(p.relative_to(DIST).parent.as_posix() for p in DIST.rglob('index.html'))
    urls = [SITE + '/' + ('' if p == '.' else p + '/') for p in pages_all]
    (DIST / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n'
                                      % ''.join('  <url><loc>%s</loc></url>\n' % u for u in urls), encoding='utf-8')
    (DIST / 'robots.txt').write_text('User-agent: *\nDisallow: /\n' if TEST else 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % SITE, encoding='utf-8')
    files = sorted(str(p.relative_to(DIST)) for p in DIST.rglob('*.html'))
    left = [f for f in files if 'data-go=' in (DIST / f).read_text(encoding='utf-8')]
    print('%d pagini în dist/ (%s)%s' % (len(files), 'test' if TEST else 'site', '; rămase cu data-go: %s' % left if left else ''))

if '--fise' in sys.argv: render_fise(ROOT / 'fise'); print('fișele PDF refăcute în fise/')
else: main()
