"""Package only the two selected styles and verify the self-contained preview."""
from pathlib import Path
import base64, hashlib, json, re, shutil, subprocess, zipfile
from pypdf import PdfReader

root = Path(__file__).parent.resolve()
expected = {'reference', 'gbt9704'}
assert {p.stem for p in (root/'output/pdf').glob('*.pdf')} == expected
html = (root/'index.html').read_text()
script = re.search(r'<script>([\s\S]*?)</script>', html)[1]
(root/'.qa/picker-syntax.js').write_text(script)
node = shutil.which('node')
if not node:
    raise RuntimeError('Node.js is required for the picker syntax check')
subprocess.run([node, '--check', str(root/'.qa/picker-syntax.js')], check=True)
editions = json.loads(re.search(r'const editions=([\s\S]*?);\nlet page=1;', script)[1])
assert {e['slug'] for e in editions} == expected and len(editions) == 2
manifest = {}
for edition in editions:
    slug = edition['slug']
    pdf = root/f'output/pdf/{slug}.pdf'
    assert len(edition['images']) == len(PdfReader(pdf).pages)
    for n, url in enumerate(edition['images'], 1):
        assert base64.b64decode(url.split(',', 1)[1]) == (root/f'previews/{slug}-{n}.png').read_bytes()
    manifest[slug] = {'pages': len(edition['images']), 'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()}
(root/'.qa/picker-static-check.json').write_text(json.dumps({
    'javascript_syntax': 'pass', 'embedded_images_match_pdf_renders': True, 'editions': manifest,
}, indent=2))

names = ['specimen.typ', 'gbt9704.typ', 'build.sh', 'preview.py', 'verify_artifacts.py', 'package.py',
         'plot.py', 'README.md', 'reference-style.md', 'gbt9704-style.md', 'index.html',
         'output/style-comparison.png', '.qa/verification.json', '.qa/picker-static-check.json']
files = [root/n for n in names]
for folder in ['assets', 'styles', 'previews', 'output/pdf']:
    files.extend(p for p in (root/folder).rglob('*') if p.is_file())
archive = root/'output/recto-book-styles.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
    for p in sorted(set(files)):
        package.write(p, 'book-styles/'+p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
    for slug in expected:
        assert package.read(f'book-styles/output/pdf/{slug}.pdf') == (root/f'output/pdf/{slug}.pdf').read_bytes()
    assert not any(n.endswith(('.ttf', '.ttc', '.otf')) for n in package.namelist())
print(f'Packed {len(files)} files, {sum(v["pages"] for v in manifest.values())} preview pages; only two styles present.')
