from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,html,zipfile
R=Path(__file__).resolve().parent
pages=json.loads((R/'page_index.json').read_text(encoding='utf-8'))
points=json.loads((R/'device_points.json').read_text(encoding='utf-8'))
qa=R/'qa';qa.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',24)
for start in range(0,len(pages),9):
    board=Image.new('RGB',(1800,1350),'#dce5df');dr=ImageDraw.Draw(board)
    for k,p in enumerate(pages[start:start+9]):
        i=start+k+1;im=Image.open(R/'pages'/f'sheet-{i:02}.png');im.thumbnail((590,417))
        x=k%3*600;y=k//3*450;board.paste(im,(x,y+30));dr.text((x+10,y+3),f'{i:02}  '+p['code'],font=font,fill='#253943')
    board.save(qa/f'contact-{start//9+1}.png')
style='''*{box-sizing:border-box}body{margin:0;background:#f3f4ef;color:#253943;font:16px/1.75 system-ui,"Microsoft YaHei",sans-serif}header{background:#153f44;color:#f6f4ea;padding:50px max(5vw,24px)}h1{font-size:clamp(30px,4vw,58px);margin:12px 0}p{max-width:1000px}.button{display:inline-block;padding:10px 20px;margin:8px 8px 8px 0;background:#e4c18b;color:#153f44;text-decoration:none;border-radius:6px}main{max-width:1450px;margin:40px auto;padding:0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}.card{background:white;color:inherit;text-decoration:none;border:1px solid #d5dfd9;border-radius:8px;overflow:hidden}.card img{width:100%;display:block}.card span{display:block;padding:12px 16px}.note{background:#e2eae3;border-left:4px solid #267178;padding:20px 25px;margin:30px 0}section{margin:50px 0}input,select{font:inherit;padding:9px;border:1px solid #bacac2;border-radius:5px}input{width:min(600px,90vw)}table{width:100%;border-collapse:collapse;background:white;font-size:14px}td,th{padding:12px;border:1px solid #d2dcd5;text-align:left;vertical-align:top}th{background:#e4ece7;position:sticky;top:0}small{color:#5b736d}.scroll{overflow:auto}a{color:#226f78}footer{padding:35px;color:#61776d}@media print{header{padding:10px;background:white;color:#253943}.controls{display:none}th{position:static}table{font-size:10px}td,th{padding:5px}}'''
gallery=''.join(f'<a class="card" href="images/{n}" target="_blank"><img src="images/{n}" alt="{title}"><span>{title}</span></a>' for n,title in [('exterior_v2.png','更新后的三层外观'),('living_v2.png','餐客厅与设备柜'),('kitchen_v2.png','厨房设备布置'),('bedroom_v2.png','老人房与床头设备')])
cards=''.join(f'<a class="card" href="pages/sheet-{i:02}.png" target="_blank"><img loading="lazy" src="pages/sheet-{i:02}.png" alt="{p["title"]}"><span>{p["code"]} · {p["title"]}</span></a>' for i,p in enumerate(pages,1))
doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>南院 V2 · 少过道与全屋智能</title><style>{style}</style><header><div>10 × 10 M / THREE FLOORS / SMART HOME</div><h1>南院 V2 · 少过道与全屋智能</h1><p>西北楼梯直接连餐客厅，楼上家庭厅兼交通。保留5卧室、书房及西南露台，新增家电、灯光窗帘、网络和传感器的安装位置。</p><a class="button" href="10x10三层住宅_V2少过道与全屋智能.pdf">打开 {len(pages)} 页完整图册</a><a class="button" href="设备点位表.html">搜索 {len(points)} 条安装点位</a><a class="button" href="#drawings">浏览高清图纸</a></header><main><div class="note"><strong>已确认：</strong>10×10米、三层、南侧入户、米家/Aqara倾向。<br><strong>待确认：</strong>常住人数、所在地、预算、空调形式、气源及具体产品型号。安装表包含候选与备用点，不等于采购数量。此版本为概念深化，非直接施工图。</div><section><h2>装修与外观示意</h2><div class="grid">{gallery}</div></section><section id="drawings"><h2>完整图纸 · 点击放大</h2><div class="grid">{cards}</div></section></main><footer>V2 / 2026.10.28 · 图册、点位表、JSON数据和绘图源码随包交付。</footer></html>'''
(R/'index.html').write_text(doc,encoding='utf-8')
rows=[]
for q in points:
    es=lambda s:html.escape(str(s))
    rows.append(f'''<tr data-floor="{q['floor']}" data-cat="{q['cat']}"><td><strong>{q['id']}</strong><br>{q['floor']}F</td><td>{es(q['name'])}<br><small>{es(q['size'])}</small></td><td>X {q['x']}<br>Y {q['y']}<br>Z {q['z']}</td><td>{es(q['power'])}</td><td>{es(q['network'])}</td><td>{es(q['note'])}</td></tr>''')
doc=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V2 硬件安装点位表</title><style>{style}</style><header><h1>硬件安装点位表</h1><p>{len(points)}条计划点位，含候选、备用和控制点，不等于{len(points)}台采购设备。原点为建筑西北外角，X向东、Y向南，Z相对本层完成地面，单位mm。</p><a class="button" href="index.html">返回图纸</a><a class="button" href="device_points.json">完整JSON数据</a></header><main><div class="note">燃气报警器 Z=0 表示高度未定，绝不是落地安装。设备中心与出线点可能不同，先核对产品安装图再放样。米家/Aqara兼容性按具体型号、地区、网关及功能确认。</div><div class="controls"><input id="q" placeholder="搜索：厨房 / 窗帘 / 空调 / F1-A01…"><select id="floor"><option value="">全部楼层</option><option value="1">一层</option><option value="2">二层</option><option value="3">三层</option></select><select id="cat"><option value="">全部类别</option><option value="A">家电与固定设备</option><option value="L">灯光、开关、窗帘</option><option value="N">网络与传感器</option></select><p id="count"></p></div><div class="scroll"><table><thead><tr><th>编号</th><th>设备 / 预留尺寸</th><th>坐标mm</th><th>供电</th><th>接入方式</th><th>安装与检修要求</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></main><script>const rows=[...document.querySelectorAll('tbody tr')];function update(){{const q=document.getElementById('q').value.toLowerCase().trim(),f=document.getElementById('floor').value,c=document.getElementById('cat').value;let n=0;rows.forEach(r=>{{let ok=(!f||r.dataset.floor===f)&&(!c||r.dataset.cat===c)&&(!q||r.textContent.toLowerCase().includes(q));r.hidden=!ok;if(ok)n++}});document.getElementById('count').textContent='显示 '+n+' / '+rows.length+' 条点位'}};['q','floor','cat'].forEach(x=>document.getElementById(x).addEventListener('input',update));update();</script></html>'''
(R/'设备点位表.html').write_text(doc,encoding='utf-8')
readme=f'''# 10×10m三层住宅 V2

已确认：10×10m、三层、南侧临路及入户；用户选择米家 / Aqara智能生态。

新布局：西北楼梯直接连公共厅；首层餐客厅净范围约29.5㎡，东侧短通道约4.0㎡；上层各有两侧短通道约8.1㎡。公共厅内仍有通行面积，不能将其当作完全零过道。

暂用假设：5–6人，5卧室＋书房，三层西南露台；分体空调、空气源热泵热水、燃气灶＋洗碗机＋蒸烤箱。常住人数、预算、地区、气源与实际设备型号待确认。

输出：{len(pages)}页A3 PDF、逐页PNG、4张建模示意、可搜索的{len(points)}条点位表、JSON数据及可重建源码。

点位A为家电/固定硬件、L为灯光/开关/窗帘、N为网络/传感器，含候选与备用；不是采购清单或计算过的电气施工图。

米家为主要入口，Aqara按具体中国大陆SKU、App支持、协议、网关和功能确认。没有声称所有Aqara产品兼容米家。基础实体操作和独立安全告警需现场验证。

此为概念深化，不是施工图。结构、基础、配筋、净空、消防、节能、最终配电整定/线径、给排水计算、气源接入与设备厂家安装条件尚待专业完成。室外设备位置未确认用地边界，不得据此占地安装。

先打开 index.html，再打开 设备点位表.html。二者均可离线浏览。完整PDF可打印A3；主要平面按A3原幅1:60，缩放打印比例会变化。

重建：Python 3.12+，依赖 reportlab、Pillow、numpy；字体 C:/Windows/Fonts/simhei.ttf。
1. 运行 build_v2.py
2. 用 Poppler pdftoppm -scale-to 1800 -png 将PDF渲染到 pages/sheet
3. 运行 package_v2.py

所有效果图为本地几何建模示意，不是AI写实照片；未调用图像API。
'''
(R/'README.md').write_text(readme,encoding='utf-8')
with zipfile.ZipFile(R.parent/'10x10三层住宅_V2少过道全屋智能_设计包.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in R.rglob('*'):
        if p.is_file() and not any(t in p.relative_to(R).parts for t in ['qa','__pycache__']):z.write(p,'house_design_v2/'+str(p.relative_to(R)))
print('Created HTML explorer, searchable points, QA contacts and ZIP')
