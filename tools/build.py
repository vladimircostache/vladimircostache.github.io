# Generează site-ul static BIG Solutions în dist/.
#   python3 tools/build.py          → adrese curate (/programe/…/), pentru bigsolutions.ro
#   python3 tools/build.py --test   → linkuri relative cu index.html, pentru linkul de test
import html, json, posixpath, re, shutil, sys, unicodedata, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DIST = ROOT / 'src', ROOT / 'dist'
TEST = '--test' in sys.argv
UPD = '29.10.2026'
SITE = 'https://bigsolutions.ro'
LEGAL_UPD = '30.10.2026'
PHONE, PHONE_TEL, WA = '0742 225 222', '+40742225222', 'https://wa.me/40742225222'

def read(rel): return (SRC / rel).read_text(encoding='utf-8')
def data(name): return json.loads(read('data/%s.json' % name))
calls, pages, programs, featured, seo = data('calls'), data('pages'), data('programs'), data('featured'), data('seo')

BL = {'deschis': 'Deschis', 'urmeaza': 'Urmează', 'consultare': 'În consultare', 'inchis': 'Închis'}
WHO = {'F': 'Firme', 'O': 'ONG-uri', 'A': 'Autorități'}
TRACKS = {'F': ('Firme', '/firme/'), 'O': ('ONG-uri', '/ong-uri/'), 'A': ('Autorități publice', '/autoritati-publice/')}
TRACK_BY_NAME = {v[0]: (k, v[1]) for k, v in TRACKS.items()}
PRE = {'F': 'firma', 'O': 'ong', 'A': 'uat'}
LEGAL = {'Politica de confidențialitate': '/politica-de-confidentialitate/', 'Politica de cookies': '/politica-cookies/', 'Termeni și condiții': '/termeni-si-conditii/'}
LEGAL_DESC = {
    'Politica de confidențialitate': 'Cum folosim datele trimise prin site: ce date, de ce, cui le transmitem, cât timp le păstrăm și ce drepturi aveți.',
    'Politica de cookies': 'Site-ul nu folosește cookie-uri de reclamă, de urmărire sau de statistică. Ce folosim în schimb și cum controlați cookie-urile.',
    'Termeni și condiții': 'Condițiile de folosire a site-ului: informațiile despre programe, verificarea eligibilității, drepturile de autor și litigiile.'}

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
    return h

def finalize(h, page_path):
    """Adresele „@/…” devin absolute (site) sau relative cu index.html (test)."""
    here = page_path.strip('/')
    def url(u):
        if not TEST: return u
        path, rest = re.match(r'([^?#]*)(.*)', u).groups()
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
        out.append('<div class="cl"><div class="meta">%s<span>%s</span></div><a class="cl-t" href="@/apeluri/%s/">%s</a><span class="cl-m">%s · %s</span></div>'
                   % (badge(c['s']), esc(when(c)), c['slug'], esc(c['n']), esc(c['prog'][-1]), esc(c['sum'])))
    return ''.join(out)
def by_slug(s): return next(c for c in calls if c['slug'] == s)

def layout(page_path, title, desc, body, scripts=''):
    body = fix_headings(strip_mock(body).replace('src="vladimir.jpg"', 'src="@/assets/img/vladimir-costache.jpg"'))
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
           '<link rel="icon" href="%s">\n<link rel="apple-touch-icon" href="@/assets/img/apple-touch-icon.png">\n<link rel="preload" href="@/assets/fonts/bricolage-grotesque-latin.woff2" as="font" type="font/woff2" crossorigin>\n'
           '<link rel="stylesheet" href="@/assets/css/site.css">\n%s</head>\n<body>\n<div class="site" id="site">\n%s\n<main id="main">\n%s\n</main>\n%s\n%s\n</div>\n%s<script src="@/assets/js/site.js" defer></script>\n</body>\n</html>\n') % (
        esc(title), esc(desc), '<meta name="robots" content="noindex">\n' if TEST else '', canonical, esc(title), esc(desc), canonical, SITE, favicon,
        JSONLD if page_path == '/' else '',
        header, body, footer, mbar, scripts)
    doc = contact_links(route_links(doc)).replace('<body>', '<body data-ix="%s">' % ('index.html' if TEST else ''), 1)
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
    feat = ''
    for c in map(by_slug, featured):
        feat += ('<div class="call"><div class="meta">%s<span>%s</span></div><h4>%s</h4><span class="who">%s</span><span class="sum">%s</span>'
                 '<a class="link" href="@%s">Pagina programului&nbsp;→</a></div>') % (badge(c['s']), esc(when(c)), esc(c['n']), esc(c['prog'][-1]), esc(c['sum']), prog_path(c['pg']))
    v = v.replace('<div class="calls" id="featured"></div>', '<div class="calls" id="featured">%s</div>' % feat)
    cards = ''
    for p in programs:
        tags = ''.join('<span class="tag">%s</span>' % WHO[t] for t in p['t'])
        cards += '<a class="prog" href="@%s" data-t="%s"><h4>%s</h4><p>%s</p><div class="tags">%s</div><span class="go">Pagina programului&nbsp;→</span></a>' % (
            prog_path(p['n']), ' '.join(p['t']), esc(p['n']), esc(p['d']), tags)
    v = v.replace('<div class="progs" id="progs"></div>', '<div class="progs" id="progs">%s</div>' % cards)
    s = seo['/']
    write_page('/', s['title'], s['description'], strip_mock(v))

# ---- pagina Autoconsum (scrisă integral în machetă)
def build_autoconsum():
    v = read('views/program.html')
    lst = sort_calls([c for c in calls if c['pg'] == 'Autoconsum și stocare' and c['s'] != 'inchis'])
    v = v.replace('<div class="cls" id="pr-calls"></div>', '<div class="cls" id="pr-calls">%s</div>' % call_list(lst, 'Nu sunt apeluri deschise acum.'))
    s = seo['/programe/autoconsum-si-stocare/']
    write_page('/programe/autoconsum-si-stocare/', s['title'], s['description'], strip_mock(v))

# ---- paginile de program și de traseu
def build_prog(name, track=None):
    v = read('views/prog.html')
    key = ('traseu:' + name) if track else name
    pg = pages[key]
    if track:
        f, path = TRACK_BY_NAME[name]
        lst = sort_calls([c for c in calls if c['s'] == 'deschis' and f in c['w'] and c['pg']])
        crumb = '<span>%s</span>' % esc(name)
        heading, preset = 'Apelurile deschise acum', PRE[f]
    else:
        pr = next(p for p in programs if p['n'] == name)
        f = pr['t'][0]; path = prog_path(name)
        lst = sort_calls([c for c in calls if c['pg'] == name and c['s'] != 'inchis'])
        tname, tpath = TRACKS[f]
        crumb = '<a href="@%s">%s</a><span>/</span><span>%s</span>' % (tpath, esc(tname), esc(name))
        heading, preset = 'Apelurile deschise și cele care urmează', pg.get('pre', PRE[f])
    n_open = sum(1 for c in lst if c['s'] == 'deschis')
    st = ('<span class="bdg b-deschis">%s</span>' % n_apel(n_open, 'apel deschis', 'apeluri deschise')) if n_open else '<span class="bdg b-inchis">Niciun apel deschis acum</span>'
    v = v.replace('<span id="pg-cr"></span>', crumb)
    v = v.replace('<span class="bdg b-consultare" id="pg-b1">Pagină în lucru</span><span id="pg-b2">Textele se scriu în Etapa 5</span>', st + '<span>Actualizat la %s</span>' % UPD)
    v = v.replace('<h1 id="pg-t"></h1>', '<h1 id="pg-t">%s</h1>' % esc(pg['t']))
    v = v.replace('<p class="lead" id="pg-l"></p>', '<p class="lead" id="pg-l">%s</p>' % esc(pg['l']))
    v = re.sub(r'\s*<p class="mocknote" id="pg-note"></p>', '', v)
    v = re.sub(r'\s*<section style="display:grid;gap:12px" id="pg-osec">.*?</section>', '', v, flags=re.S)
    body = pg['h'].replace('class="btn ink prep-elig" href="#eligibilitate" data-go="eligibilitate"', 'class="btn ink prep-elig" href="#eligibilitate" data-go="eligibilitate" data-preset="%s"' % preset)
    v = v.replace('<div class="pmain" id="pg-full" hidden></div>', '<div class="pmain" id="pg-full">%s</div>' % body)
    v = v.replace('id="pg-ch">Apelurile deschise și cele care urmează<', 'id="pg-ch">%s<' % heading)
    v = v.replace('<div class="cls" id="pg-calls"></div>', '<div class="cls" id="pg-calls">%s</div>' % call_list(lst, 'Nu sunt apeluri deschise acum. Când apare unul, îl vedeți aici și în calendar.'))
    v = v.replace('data-go="eligibilitate" id="pg-elig"', 'data-go="eligibilitate" data-preset="%s" id="pg-elig"' % preset)
    s = seo[path]
    write_page(path, s['title'], s['description'], v)

# ---- fișa fiecărui apel
def build_call(c):
    v = read('views/apel.html')
    st = badge(c['s']) + '<span>%s</span><span>Actualizat la %s</span>' % (esc(when(c)), UPD)
    facts = [[(c['open'] + ' – ' + c['close']) if c['open'] and c['close'] else when(c), 'perioada de depunere'], [c['sum'], 'buget'], [BL[c['s']], 'starea apelului'], [c['tip'], 'tipul apelului']] + (c.get('extra') or [])
    fh = ''.join('<div><b>%s</b><span>%s</span></div>' % (esc(a), esc(b)) for a, b in facts)
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
           'id="ap-full"></p>': 'id="ap-full">%s</p>' % esc(c['full']),
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
    write_page('/apeluri/%s/' % c['slug'], title, desc, strip_mock(v))

# ---- calendar, eligibilitate, despre, contact, pagini legale (în lucru), 404
def build_rest():
    keep = ['n', 'prog', 'w', 's', 'open', 'close', 'when', 'sum', 'slug']
    def plain(t): return ''.join(ch for ch in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(ch) != 'Mn')
    rows = [dict({k: c.get(k) for k in keep}, q=plain(' '.join([c['n'], ' '.join(c['prog']), c.get('full', ''), c.get('rez', ''), ' '.join(c.get('ben') or [])]))) for c in calls]
    data_js = '<script>window.CALLS=%s;</script>\n' % json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    write_page('/apeluri/', 'Calendar apeluri de finanțare | BIG Solutions',
               'Apelurile deschise și cele care urmează din programele pe care lucrăm: cine poate aplica, termenul și bugetul. Actualizat săptămânal.',
               read('views/apeluri.html'), data_js)
    write_page('/verifica-eligibilitatea/', 'Verifică eligibilitatea | BIG Solutions',
               'În 4 pași aflați dacă proiectul dumneavoastră poate primi finanțare. Discuția de principiu e gratuită.', read('views/eligibilitate.html'))
    for path, view in [('/despre-noi/', 'despre'), ('/contact/', 'contact')]:
        v = read('views/%s.html' % view).replace('src="vladimir.jpg"', 'src="@/assets/img/vladimir-costache.jpg"')
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

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(SRC / 'assets', DIST / 'assets')
    build_home(); build_autoconsum()
    for p in programs:
        if p['n'] != 'Autoconsum și stocare': build_prog(p['n'])
    for t in TRACK_BY_NAME: build_prog(t, track=True)
    for c in calls: build_call(c)
    build_rest()
    pages_all = sorted(p.relative_to(DIST).parent.as_posix() for p in DIST.rglob('index.html'))
    urls = [SITE + '/' + ('' if p == '.' else p + '/') for p in pages_all]
    (DIST / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n'
                                      % ''.join('  <url><loc>%s</loc></url>\n' % u for u in urls), encoding='utf-8')
    (DIST / 'robots.txt').write_text('User-agent: *\nDisallow: /\n' if TEST else 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % SITE, encoding='utf-8')
    files = sorted(str(p.relative_to(DIST)) for p in DIST.rglob('*.html'))
    left = [f for f in files if 'data-go=' in (DIST / f).read_text(encoding='utf-8')]
    print('%d pagini în dist/ (%s)%s' % (len(files), 'test' if TEST else 'site', '; rămase cu data-go: %s' % left if left else ''))

main()
