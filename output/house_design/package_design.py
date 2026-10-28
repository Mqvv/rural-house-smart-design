from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,html,zipfile

root=Path(__file__).resolve().parent
pages=json.loads((root/'page_index.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',24)
qa=root/'qa';qa.mkdir(exist_ok=True)
for start in range(0,len(pages),9):
    board=Image.new('RGB',(1800,1350),'#d9e3e0');d=ImageDraw.Draw(board)
    for k,pg in enumerate(pages[start:start+9]):
        i=start+k+1;im=Image.open(root/'pages'/f'sheet-{i:02}.png');im.thumbnail((590,417))
        x=(k%3)*600;y=(k//3)*450;board.paste(im,(x,y+30));d.text((x+10,y+3),f'{i:02}  '+pg['code'],font=font,fill='#253943')
    board.save(qa/f'contact-{start//9+1}.png')

cards=''.join(f'<a class="card" href="pages/sheet-{i:02}.png" target="_blank"><img loading="lazy" src="pages/sheet-{i:02}.png"><span>{p["code"]} · {html.escape(p["title"])}</span></a>' for i,p in enumerate(pages,1))
gallery=''.join(f'<a href="images/{f}" target="_blank"><img src="images/{f}"></a>' for f in ['01_现代简约.png','02_新中式.png','03_乡村坡屋顶.png','living.png','bedroom.png','kitchen.png'])
doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南院 · 三层乡居</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f4ef;color:#253943;font:16px/1.8 system-ui,"Microsoft YaHei",sans-serif}header{padding:64px max(5vw,24px);background:#143e43;color:#f5f3e9}h1{font-size:clamp(32px,5vw,65px);margin:12px 0}h2{font-size:26px}p{max-width:900px}main{max-width:1440px;margin:50px auto;padding:0 26px}.tag{letter-spacing:3px;color:#b6cfca}.button{display:inline-block;background:#e7c48e;color:#183b40;padding:12px 23px;border-radius:6px;text-decoration:none;margin:12px 12px 0 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}.grid img{width:100%;display:block}.card{background:white;color:inherit;text-decoration:none;border-radius:8px;overflow:hidden;border:1px solid #d4dfda}.card span{display:block;padding:12px 18px;font-weight:600}.note{padding:22px 28px;background:#e5ebe5;border-left:4px solid #276c70;margin:30px 0}footer{padding:30px;color:#62757c}section{margin:60px 0}
</style><header><div class="tag">10 × 10 M / SOUTH ENTRY / THREE FLOORS</div><h1>南院 · 三层乡居</h1><p>南向入户，首层老人房，5间卧室与书房，三层西南露台。25页建筑、装修与水电网气概念图册，附3种外观和3张室内轴测示意。</p><a class="button" href="10x10三层住宅_方案与装修机电图册.pdf">打开完整 PDF</a><a class="button" href="#drawings">浏览全部图纸</a></header><main><div class="note"><strong>方案范围</strong><br>已确认10×10米、三层及南侧临路；常住人数、风格、预算和气源尚待确认。本册是概念深化，尚无结构计算、设备容量或审批验证，不能直接用于施工。外观为几何建模示意，不是写实照片。</div><section><h2>外观与装修意向</h2><div class="grid">GALLERY</div></section><section id="drawings"><h2>全套图纸 · 点击放大</h2><div class="grid">CARDS</div></section></main><footer>2026.10.28 · A3图册 · 设计参数及绘图源代码随包提供</footer></html>'''
(root/'index.html').write_text(doc.replace('GALLERY',gallery).replace('CARDS',cards),encoding='utf-8')
with zipfile.ZipFile(root.parent/'10x10三层住宅_设计方案包.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file() and 'qa' not in p.relative_to(root).parts and p.suffix!='.pyc':z.write(p,'house_design/'+str(p.relative_to(root)))
print('Packaged',len(pages),'pages and 6 model images')
