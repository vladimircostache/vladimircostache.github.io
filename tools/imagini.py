# Redimensionează imagini și le salvează în JPEG și WebP, cu Chrome (fără alte programe).
# Folosire: python3 tools/imagini.py sursa.jpg destinatie-fara-extensie LATIME[xINALTIME] [LATIME...]
#   ex.: python3 tools/imagini.py crop43.jpg src/assets/img/scoala-panouri 1000x750 640x480
# Pentru fiecare dimensiune scrie <destinatie>-<latime>.webp și .jpg (sau <destinatie>.webp/.jpg cu o singură dimensiune și --fara-latime).
import base64, json, pathlib, re, subprocess, sys, tempfile

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
src, dest, sizes = pathlib.Path(sys.argv[1]), sys.argv[2], [a for a in sys.argv[3:] if not a.startswith('--')]
plain = '--fara-latime' in sys.argv
mime = 'image/png' if src.suffix.lower() == '.png' else 'image/jpeg'
dims = [tuple(int(x) for x in s.split('x')) if 'x' in s else (int(s), None) for s in sizes]
html = '''<!doctype html><meta charset="utf-8"><body><pre id="out"></pre><img id="i" src="data:%s;base64,%s"><script>
const i=document.getElementById('i');i.onload=()=>{const r={};for(const [w,h0] of %s){const h=h0||Math.round(w*i.naturalHeight/i.naturalWidth);
const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.imageSmoothingQuality='high';
const s=Math.max(w/i.naturalWidth,h/i.naturalHeight),sw=w/s,sh=h/s;x.drawImage(i,(i.naturalWidth-sw)/2,(i.naturalHeight-sh)/2,sw,sh,0,0,w,h);
r[w]={webp:c.toDataURL('image/webp',0.78),jpg:c.toDataURL('image/jpeg',0.8)};}document.getElementById('out').textContent=JSON.stringify(r);i.remove();};
</script>''' % (mime, base64.b64encode(src.read_bytes()).decode(), json.dumps(dims))
with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f: f.write(html)
dom = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--virtual-time-budget=8000', '--dump-dom', 'file://' + f.name],
                     capture_output=True, text=True).stdout
pathlib.Path(f.name).unlink()
res = json.loads(re.search(r'<pre id="out">(.*?)</pre>', dom, re.S).group(1).replace('&quot;', '"'))
for w, r in res.items():
    for ext in ('webp', 'jpg'):
        out = pathlib.Path('%s%s.%s' % (dest, '' if plain else '-' + w, ext))
        out.write_bytes(base64.b64decode(r[ext].split(',', 1)[1]))
        print(out, out.stat().st_size // 1024, 'KB')
