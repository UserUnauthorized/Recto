"""Check deliverable PDFs and the measured GB/T body, folio and table geometry."""
from pathlib import Path
from collections import Counter
import json, math, re, subprocess
import pdfplumber

root = Path(__file__).parent.resolve()
mm = 72 / 25.4
checks = {'compiler': (root/'.qa/compiler-version.txt').read_text().strip(), 'editions': {}}
anchors = {
    'reference': ['从变化率到局部模型', '二阶Taylor公式', '指数函数的二阶近似',
                  '误差的尺度与可视化', '多元情形与二次型', '练习与进一步思考'],
    'gbt9704': ['课程资料整理与使用说明', '（一）保持内容完整', '（1）保留必要的对应信息',
                '附件1', '附件2', '课程资料登记表', '学习材料对照表（续）'],
}
for slug, required in anchors.items():
    assert not (root/f'.qa/{slug}.log').read_text().strip(), f'Compiler diagnostics: {slug}'
    content = re.sub(r'\s+', '', (root/f'.qa/{slug}.txt').read_text())
    assert all(t in content for t in required), (slug, 'missing text')
    assert '\ufffd' not in content, (slug, 'replacement glyph')
    with pdfplumber.open(root/f'output/pdf/{slug}.pdf') as pdf:
        outside = []
        for n, page in enumerate(pdf.pages, 1):
            for ch in page.chars:
                if ch['x0'] < -.1 or ch['x1'] > page.width+.1 or ch['top'] < -.1 or ch['bottom'] > page.height+.1:
                    outside.append((n, ch['text']))
        assert not outside, (slug, outside)
        fonts = (root/f'.qa/{slug}-fonts.txt').read_text().splitlines()[2:]
        embedding = [re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line).group(1)
                     for line in fonts if line.strip()]
        assert embedding and all(v == 'yes' for v in embedding)
        checks['editions'][slug] = {'pages': len(pdf.pages), 'size_pt': [pdf.pages[0].width, pdf.pages[0].height],
            'embedded_fonts': len(embedding), 'missing_anchors': 0, 'out_of_page_characters': 0, 'compiler_diagnostics': 0}

# A plain CJK calibration page verifies the 22 x 28 result, not just set-rule values.
qa = root/'.qa/gbt9704'
qa.mkdir(exist_ok=True)
(qa/'grid-probe.typ').write_text('#import "../../styles/gbt9704.typ": gbt-layout\n#show: gbt-layout\n#set par(first-line-indent: 0pt)\n#for i in range(616) { [字] }\n')
subprocess.run(['typst', 'compile', '--root', str(root), str(qa/'grid-probe.typ'), str(qa/'grid-probe.pdf')], check=True, capture_output=True)
with pdfplumber.open(qa/'grid-probe.pdf') as pdf:
    assert len(pdf.pages) == 1
    rows = Counter(round(c['top'], 2) for c in pdf.pages[0].chars if c['text'] == '字')
    assert len(rows) == 22 and set(rows.values()) == {28}, rows
    checks['gbt_grid_probe'] = {'lines': len(rows), 'characters_per_line': 28}

with pdfplumber.open(root/'output/pdf/gbt9704.pdf') as pdf:
    assert len(pdf.pages) == 5
    folios = []
    for n, page in enumerate(pdf.pages, 1):
        assert abs(page.width-210*mm) < .01 and abs(page.height-297*mm) < .01
        chars = [c for c in page.chars if c['text'].strip()]
        folio = [c for c in chars if 'SimSun' in c['fontname'] and c['top'] > 750]
        assert ''.join(c['text'] for c in folio) == str(n)
        assert all(abs(c['size']-14) < .01 and c['upright'] for c in folio)
        rules = [r for r in page.rects if r['top'] > 750 and abs(r['width']-14) < .01]
        assert len(rules) == 2 and all(abs(r['top']-269*mm) < .01 for r in rules)
        if n % 2:
            assert abs(max(r['x1'] for r in rules)-(184*mm-14)) < .01
        else:
            assert abs(min(r['x0'] for r in rules)-(28*mm+14)) < .01
        body = [c for c in chars if c not in folio]
        # Font glyph bounds may protrude slightly from text frames; use the standard's 1mm tolerance.
        assert min(c['x0'] for c in body) >= 27*mm
        # Closing CJK punctuation has a full-em PDF advance box even when Typst
        # compresses its blank right half; inspect the visible half, plus PNGs.
        assert max(c['x1'] - (c['size']/2 if abs(c['matrix'][1]) < 1e-6 and c['text'] in '。，；：！？' else 0)
                   for c in body) <= 185*mm
        assert min(c['top'] for c in body) >= 36*mm
        assert max(c['bottom'] for c in body) <= 263*mm
        assert all(c['non_stroking_color'] in [(0,), (0, 0, 0), 0] for c in chars)
        folios.append({'page': n, 'position': 'right' if n % 2 else 'left', 'rule_top_mm': 269})
    # Font roles, title centering, two-character heading indent and third-row attachment title.
    first = pdf.pages[0]
    title = [c for c in first.chars if 'FZXBSK' in c['fontname']]
    assert title and all(abs(c['size']-22) < .01 for c in title)
    assert abs((min(c['x0'] for c in title)+max(c['x1'] for c in title))/2-106*mm) < .05
    for prefix, font in [('一、', 'FZHTK'), ('（一）', 'FZKTK'), ('1.', 'FZFSK'), ('（1）', 'FZFSK')]:
        row = next(w for w in first.extract_words(extra_attrs=['fontname', 'size']) if w['text'].startswith(prefix))
        assert font in row['fontname'] and abs(row['size']-16) < .01
        assert abs(row['x0']-(28*mm+2*(16+(156*mm-28*16)/27))) < .05
    annex_title = [c for c in pdf.pages[2].chars if 'FZXBSK' in c['fontname']]
    line_step = 16 + (225*mm-22*16)/21
    assert abs(min(c['top'] for c in annex_title)-min(c['top'] for c in title)-2*line_step) < .05
    orientation = []
    for n in [4, 5]:
        p = pdf.pages[n-1]
        logical = ''.join(c['text'] for c in p.chars)
        start = logical.index('学习单元')
        header = p.chars[start:start+4]
        x = sum((c['x0']+c['x1'])/2 for c in header)/4
        assert all(abs(c['matrix'][0]) < 1e-6 and abs(abs(c['matrix'][1])-1) < 1e-6 for c in header)
        assert (x > p.width/2) if n % 2 == 0 else (x < p.width/2)
        orientation.append({'page': n, 'header_side': 'cut/right' if n % 2 == 0 else 'binding/left'})
    checks['gbt_layout'] = {'body_frame_mm': [28, 37, 156, 225], 'folio_checks': folios,
        'heading_fonts_and_indents': 'pass', 'title_and_attachment_position': 'pass', 'landscape_headers': orientation,
        'text_color': 'black'}

checks['sine_table'] = []
for x, expected in [(0.25, '8.126e-06'), (.5, '2.589e-04'), (1, '8.138e-03')]:
    error = abs(math.sin(x)-(x-x**3/6))
    assert f'{error:.3e}' == expected and error <= x**5/120
    checks['sine_table'].append({'x': x, 'actual': error, 'upper': x**5/120})
checks['scope'] = 'Rendered specimen layout; excludes physical printing, binding and long-document acceptance.'
(root/'.qa/verification.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2))
print(json.dumps(checks, ensure_ascii=False, indent=2))
