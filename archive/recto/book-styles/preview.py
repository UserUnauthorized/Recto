"""Create an offline picker from every rendered page, including flowing layouts."""
from pathlib import Path
import base64
import json
import os
import re
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).parent
css = (root/'assets/picker.css').read_text()
js = (root/'assets/picker.js').read_text()
styles = [
    ('reference', '清爽课程讲义', '课程讲义', 'A4 · 宋体 / Times · 12pt 正文 · 居中页码'),
    ('gbt9704', '国标正文样式', '国标正文', 'GB/T 9704—2012 · 正文 / 表格 / 附件'),
]
editions = []
for slug, title, label, desc in styles:
    paths = sorted((root/'previews').glob(f'{slug}-*.png'),
                   key=lambda p: int(re.search(r'-(\d+)$', p.stem)[1]))
    assert paths, f'No rendered pages for {slug}'
    images = ['data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode() for p in paths]
    editions.append(dict(slug=slug, title=title, desc=desc, images=images))

html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recto · 排版样张</title><style>
*{box-sizing:border-box}body{margin:0;background:#e9e9e7;color:#202020;font-family:system-ui,-apple-system,sans-serif}
header{padding:22px 28px;background:#fafaf9;border-bottom:1px solid #d6d6d3;display:flex;flex-wrap:wrap;align-items:center;gap:12px 24px}
header strong{font-size:18px;letter-spacing:.05em}header span{font-size:13px;color:#626260}
.page-picker{display:flex;align-items:center;gap:6px;margin-left:auto;font-size:13px;flex-wrap:wrap}
.page-picker button{font:inherit;border:1px solid #ccc;background:white;border-radius:5px;padding:6px 11px;cursor:pointer;color:#333}
.page-picker button[aria-current=true]{background:#303030;color:white;border-color:#303030}
.details{max-width:960px;margin:20px auto 12px;padding:0 20px;display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.details strong{font-size:16px}.details span{font-size:12px;color:#646461}.details a{margin-left:auto;color:#363633;font-size:13px;text-underline-offset:4px}
.sheet{display:block;width:min(100% - 40px,920px);height:auto;margin:0 auto 95px;box-shadow:0 1px 7px #0002;background:white}
@media(max-width:600px){header{padding:16px}.page-picker{margin-left:0;width:100%}.sheet{width:calc(100% - 20px)}.details{padding:0 12px}}
''' + css + '''
@media(max-width:420px){.proto-picker-item{padding:0 8px;font-size:12px}}
</style><header><strong>Recto / 排版样张</strong><span>课程讲义与国标正文 · 两种用途，两套样式</span><div class="page-picker" aria-label="样张页码"></div></header>
<main id="stage" aria-live="polite"></main>
<nav class="proto-picker" aria-label="排版风格"><span class="proto-picker-highlight" aria-hidden="true"></span>''' + ''.join(
    f'<button class="proto-picker-item"{(" data-active aria-current=true" if i==0 else "")}>{label}</button>'
    for i, (_, _, label, _) in enumerate(styles)
) + '''</nav>
<script>const editions=''' + json.dumps(editions, ensure_ascii=False) + ''';
let page=1;
function renderEdition(e) {
  page=Math.max(1,Math.min(page,e.images.length));
  document.querySelector('.page-picker').innerHTML='<span>页码</span>'+e.images.map((_,i)=>`<button data-page="${i+1}" aria-label="第 ${i+1} 页" aria-current="${i+1===page}">${i+1}</button>`).join('');
  return `<div class="details"><strong>${e.title}</strong><span>${e.desc} / 第 ${page} / ${e.images.length} 页</span><a href="output/pdf/${e.slug}.pdf" target="_blank" rel="noopener">打开 PDF ↗</a></div><img class="sheet" src="${e.images[page-1]}" alt="${e.title}，第 ${page} 页，共 ${e.images.length} 页">`;
}
const variants=editions.map(e=>()=>renderEdition(e));
''' + js + '''
document.querySelector('.page-picker').addEventListener('click',e=>{
  const button=e.target.closest('[data-page]');
  if(!button)return;
  page=Number(button.dataset.page);
  mount(current);
});
</script></html>'''
(root/'index.html').write_text(html)

fontpath = os.environ.get('PREVIEW_FONT', str(Path.home()/'Library/Fonts/NotoSansCJKsc-Regular.otf'))
font = ImageFont.truetype(fontpath, 29)
small = ImageFont.truetype(fontpath, 18)
sheet = Image.new('RGB',(len(styles)*610+30,1030),'#ededeb')
draw = ImageDraw.Draw(sheet)
for i,(slug,title,label,desc) in enumerate(styles):
    x=30+i*610
    draw.text((x+8,20), title,font=font,fill='#222222')
    draw.text((x+8,65), desc,font=small,fill='#666666')
    im=Image.open(root/f'previews/{slug}-1.png').convert('RGB')
    im.thumbnail((580,880), Image.Resampling.LANCZOS)
    sheet.paste(im,(x+(580-im.width)//2,112))
(root/'output').mkdir(exist_ok=True)
sheet.save(root/'output/style-comparison.png')
print('Updated picker:', ', '.join(f"{e['slug']}={len(e['images'])} pages" for e in editions))
