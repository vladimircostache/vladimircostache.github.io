# Extrage designul, textele și datele din machetele aprobate (Etapa 5) în fișierele sursă ale site-ului.
# Se rulează o singură dată, la pornirea Etapei 6. După asta, sursa de adevăr sunt fișierele din src/.
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
mock_path, continut_path = sys.argv[1], sys.argv[2]
mock = open(mock_path, encoding='utf-8').read()
continut = open(continut_path, encoding='utf-8').read()

def write(rel, text):
    p = SRC / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

# ---- stiluri: fără bara machetei și fără fereastra de browser simulată
css = mock[mock.index('<style>') + 7: mock.index('</style>')]
a = css.index('/* bara de lucru a machetei')
b = css.index('.stage.phone .urlbar i{display:none}') + len('.stage.phone .urlbar i{display:none}')
css = css[:a] + css[b:]
css = re.sub(r'/\* Machetă interactivă[^*]*\*/\n', '', css)
css = css.replace('body{margin:0;background:var(--desk);', 'body{margin:0;background:var(--white);')
fonts = ''
for fam, file_base, weights in [('Bricolage Grotesque', 'bricolage-grotesque', '700 800'), ('Hanken Grotesk', 'hanken-grotesk', '400 700')]:
    fonts += ("@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;src:url(../fonts/%s-latin-ext.woff2) format('woff2');"
              "unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C4,U+2113,U+2C60-2C7F,U+A720-A7FF}\n" % (fam, weights, file_base))
    fonts += ("@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;src:url(../fonts/%s-latin.woff2) format('woff2');"
              "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}\n" % (fam, weights, file_base))
write('assets/css/site.css', '/* BIG Solutions Management – stilul Solar (Etapa 3), preluat din machetele aprobate. */\n' + fonts + css.strip() + '\n')

# ---- bucăți comune
def between(start, end, s=mock):
    i = s.index(start); j = s.index(end, i) + len(end)
    return s[i:j]
write('partials/header.html', between('<header class="hdr">', '</header>'))
write('partials/footer.html', between('<footer class="ftr">', '</footer>'))
write('partials/cookie.html', between('<div class="cookie" id="cookie"', '</div>\n    </div>'))
write('partials/mbar.html', between('<nav class="mbar"', '</nav>'))

# ---- paginile, din vederile machetei
for m in re.finditer(r'<main id="v-([a-z]+)" class="view"(?: hidden)?>(.*?)\n    </main>', mock, re.S):
    write('views/%s.html' % m.group(1), m.group(2).strip('\n') + '\n')

# ---- date
def js_value(name):
    i = mock.index('var %s=' % name) + len('var %s=' % name)
    val, _ = json.JSONDecoder().raw_decode(mock[i:])
    return val
write('data/calls.json', json.dumps(js_value('calls'), ensure_ascii=False, indent=1))
write('data/pages.json', json.dumps(js_value('PAGES'), ensure_ascii=False, indent=1))
progs = []
for m in re.finditer(r"\{n:'([^']+)',d:'([^']+)',t:\[([^\]]*)\]\}", mock):
    progs.append({'n': m.group(1), 'd': m.group(2), 't': re.findall(r"'([A-Z])'", m.group(3))})
write('data/programs.json', json.dumps(progs, ensure_ascii=False, indent=1))
feat = re.search(r"var FEAT=\[([^\]]*)\]", mock).group(1)
write('data/featured.json', json.dumps(re.findall(r"'([^']+)'", feat), ensure_ascii=False, indent=1))

# ---- titlurile și descrierile pentru Google, din SITE BIG - CONTINUT.md
seo = {}
for m in re.finditer(r'^#{2,3} [^\n]*?`(/[^`]*)`[^\n]*\n(.*?)(?=^#{2,3} |\Z)', continut, re.S | re.M):
    path, body = m.group(1), m.group(2)
    g = re.search(r'Pentru Google\*\*\n(.*?)(?:\n\n|\Z)', body, re.S)
    if not g: continue
    t = re.search(r'Titlu[^„]*„([^”]+)”', g.group(1)); d = re.search(r'Descriere[^„]*„([^”]+)”', g.group(1))
    if t and d: seo[path] = {'title': t.group(1), 'description': d.group(1)}
write('data/seo.json', json.dumps(seo, ensure_ascii=False, indent=1))
print('stiluri, %d vederi, %d apeluri, %d pagini de text, %d programe, %d titluri SEO' % (
    len(list((SRC / 'views').glob('*.html'))), len(js_value('calls')), len(js_value('PAGES')), len(progs), len(seo)))
