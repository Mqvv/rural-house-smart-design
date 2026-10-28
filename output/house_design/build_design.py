from pathlib import Path
import math, json, html
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color, white

ROOT = Path(__file__).resolve().parent
IMG = ROOT/'images'; IMG.mkdir(exist_ok=True)
PAGES = ROOT/'pages'; PAGES.mkdir(exist_ok=True)
FONT = 'C:/Windows/Fonts/simhei.ttf'
pdfmetrics.registerFont(TTFont('CN',FONT))
W,H = landscape(A3)
INK='#253943'; TEAL='#186d71'; MUTED='#62757c'; PALE='#edf3f2'; GOLD='#b68b52'
COL={'C':'#167cb5','H':'#d65547','D':'#80583b','R':'#3a9184','E':'#b54e39','L':'#ce9d21','N':'#7958a5','G':'#c8801d'}
S=1000*mm/60; OX=100; OY=687
pages=[]

def font(size): return ImageFont.truetype(FONT,size)
def rgb(c): return tuple(int(c[i:i+2],16) for i in (1,3,5))
def shade(c,k): return tuple(min(255,int(v*k)) for v in rgb(c))

class Model:
    def __init__(self): self.faces=[]
    def face(self,pts,col): self.faces.append((pts,col))
    def box(self,x,y,z,dx,dy,dz,col):
        self.face([(x,y+dy,z),(x+dx,y+dy,z),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)],shade(col,.88))
        self.face([(x+dx,y,z),(x+dx,y+dy,z),(x+dx,y+dy,z+dz),(x+dx,y,z+dz)],shade(col,.72))
        self.face([(x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)],shade(col,1.08))
    def southwindow(self,x,y,z,w,h):
        self.box(x,y,z,w,.075,h,'#283e49')
        self.box(x+.08,y+.08,z+.08,w-.16,.018,h-.16,'#789ca7')
        self.box(x+w/2-.025,y+.105,z+.08,.05,.025,h-.16,'#d0d7d4')
    def eastwindow(self,x,y,z,w,h):
        self.box(x,y,z,.075,w,h,'#283e49')
        self.box(x+.08,y+.08,z+.08,.018,w-.16,h-.16,'#789ca7')
        self.box(x+.105,y+w/2-.025,z+.08,.025,.05,h-.16,'#d0d7d4')
    def render(self,path,title,subtitle,size=(2000,1500), scale=82, center=(1000,1130)):
        im=Image.new('RGB',size,'#eef0e9')
        raw=np.array([[.80*p[0]-.60*p[1],.33*p[0]+.44*p[1]-.835*p[2]] for f in self.faces for p in f[0]])
        lo=raw.min(axis=0);hi=raw.max(axis=0)
        scale=min((size[0]-170)/(hi[0]-lo[0]),(size[1]-350)/(hi[1]-lo[1]))
        center=((size[0]-(hi[0]+lo[0])*scale)/2,185-lo[1]*scale)
        def proj(p):
            x,y,z=p; return (center[0]+scale*(.80*x-.60*y),center[1]+scale*(.33*x+.44*y-.835*z))
        # True depth buffer prevents large walls/floors from hiding foreground details.
        pixels=np.array(im);depth=np.full((size[1],size[0]),-1e8,dtype=np.float32)
        for pts,col in self.faces:
            pp=np.array([proj(p) for p in pts]);zz=np.array([.501*p[0]+.668*p[1]+.55*p[2] for p in pts])
            for ids in [(0,1,2),(0,2,3)] if len(pts)==4 else [(0,1,2)]:
                tri=pp[list(ids)];z=zz[list(ids)]
                xmin=max(0,int(math.floor(tri[:,0].min())));xmax=min(size[0]-1,int(math.ceil(tri[:,0].max())))
                ymin=max(0,int(math.floor(tri[:,1].min())));ymax=min(size[1]-1,int(math.ceil(tri[:,1].max())))
                if xmin>xmax or ymin>ymax:continue
                a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-6:continue
                yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1]
                u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
                v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
                w=1-u-v;dd=u*z[0]+v*z[1]+w*z[2]
                target=depth[ymin:ymax+1,xmin:xmax+1];mask=(u>=-1e-5)&(v>=-1e-5)&(w>=-1e-5)&(dd>=target-1e-5)
                target[mask]=dd[mask];pixels[ymin:ymax+1,xmin:xmax+1][mask]=col
        im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
        d.rectangle((0,0,size[0],150),fill='#f8f8f2')
        d.text((75,37),title,font=font(43),fill=INK)
        d.text((78,99),subtitle,font=font(22),fill=MUTED)
        d.rectangle((0,size[1]-78,size[0],size[1]),fill='#f8f8f2')
        d.text((75,size[1]-54),'尺寸约束三维示意 · 材质与采光为表达效果 · 非实景照片',font=font(23),fill=MUTED)
        im.save(path)

def exterior(style):
    m=Model(); m.box(-1,-1,-.30,12,13,.20,'#d9ded2')
    m.box(0,0,-.1,10,10,.1,'#a9aaa2')
    wall=['#e6e1d6','#eeeae1','#ddd5c5'][style]
    m.box(0,0,0,10,10,6.9,wall)
    m.box(0,0,6.9,10,6,3.3,wall); m.box(3.6,6,6.9,6.4,4,3.3,wall)
    # Plinth and floor bands match the storey levels.
    for z in [.0,3.48,6.78]: m.box(0,0,z,10.02,10.02,.12,'#adafa7' if style==0 else '#686e6b')
    for z in [0,3.6]:
        m.southwindow(.75,10.02,z+.85,2.15,1.95)
        m.southwindow(7.0,10.02,z+.85,2.05,1.95)
        if z: m.southwindow(4.05,10.02,z+.85,1.75,1.95)
    m.southwindow(4.05,10.03,.02,1.5,2.65)
    m.southwindow(7.0,10.02,7.75,2.05,1.95)
    m.southwindow(4.05,10.02,7.75,1.75,1.95)
    m.southwindow(.75,6.02,7.75,2.15,1.95)
    m.eastwindow(3.6,7.0,6.92,1.8,2.55)
    for z in [0,3.6,6.9]:
        m.eastwindow(10.02,1.0,z+1.6,1.1,.75)
        m.eastwindow(10.02,3.5,z+1.15,.85,1.15)
        m.eastwindow(10.02,7.1,z+.85,1.8,1.95)
    # Roof parapets and terrace parapets, all within footprint.
    for x,y,dx,dy in [(0,0,10,.18),(9.82,0,.18,10),(3.6,9.82,6.4,.18),(3.6,6,.18,4),(0,5.82,3.6,.18),(0,0,.18,6)]:
        if style==2 and y<6:continue
        m.box(x,y,10.2,dx,dy,1.1,'#ebe8df' if style==0 else '#646b68')
    m.box(0,6,6.9,.18,4,1.1,'#d5d0c2'); m.box(0,9.82,6.9,3.6,.18,1.1,'#d5d0c2')
    for k in range(7): m.box(.25+k*.47,9.83,7.2,.045,.07,.8,'#525e61')
    m.box(0,9.8,8.0,3.6,.22,.07,'#555d5f')
    if style==0:
        m.box(6.25,10.045,.5,.28,.10,9.45,'#937351')
        m.box(3.85,9.96,2.75,2,.04,.1,'#263e46')
    if style==1:
        for z in [3.4,6.7,10.2]:
            m.box(0,9.80,z,10,.20,.18,'#3b4647')
        for x in [.4,3.2,6.6,9.4]: m.box(x,10.04,.5,.11,.06,9.6,'#6b5742')
    if style==2:
        # Concept pitched roof over rear volume; subject to structural/local height review.
        m.face([(0,0,10.3),(10,0,10.3),(10,3,12),(0,3,12)],rgb('#7c817d'))
        m.face([(0,3,12),(10,3,12),(10,6,10.3),(0,6,10.3)],rgb('#666f70'))
        m.face([(10,0,10.3),(10,6,10.3),(10,3,12)],rgb(wall))
        m.box(3.6,6,10.2,6.4,4,.18,'#686f6c')
    # Entry steps are landscape placeholders outside 10x10 footprint.
    for i in range(3): m.box(3.8-i*.10,10.1+i*.25,-.15-i*.15,2+i*.2,.5,.15,'#b6b4a9')
    for x,y in [(-.6,10.8),(10.4,10.6),(.7,11.4)]:
        m.box(x,y,-.12,.7,.7,.55,'#b3a48b'); m.box(x+.06,y+.06,.43,.58,.58,.65,'#71856a')
    names=['01_现代简约','02_新中式','03_乡村坡屋顶']
    title=['方案 A / 现代简约','方案 B / 新中式外观','方案 C / 乡村坡屋顶意向'][style]
    m.render(IMG/(names[style]+'.png'),title,'10 × 10 m  |  3 层  |  南向入户  |  西南露台',scale=70,center=(900,980))

def interior(kind):
    m=Model()
    if kind=='living':
        # Exact living/dining clear zone, x .24..3.48, y 3.52..9.76.
        a,b=3.24,6.24
        m.box(0,0,-.12,a,b,.12,'#c5b294');m.box(0,0,0,a,.10,2.8,'#e6dfd1');m.box(0,0,0,.10,b,2.8,'#e4dfd4')
        for x in [i*.27 for i in range(13)]:m.box(x,0,.002,.007,b,.005,'#ad987c')
        m.box(.30,.25,0,1.6,.8,.75,'#b1936d')
        for x in [.38,1.25]:
            for y in [.05,1.16]:m.box(x,y,0,.47,.47,.46,'#7f897b');m.box(x,y+.4,.4,.47,.06,.45,'#7f897b')
        m.box(.15,3.60,0,.82,2.2,.38,'#c8b69d');m.box(.15,3.6,.38,.20,2.2,.45,'#b4a085')
        for y in [3.72,4.42,5.12]:m.box(.35,y,.38,.6,.63,.17,'#e1d6c2')
        m.box(1.20,4.15,.04,.65,1.05,.35,'#8c755a')
        m.box(2.80,3.7,0,.36,1.9,.43,'#a68964');m.box(3.13,3.95,.65,.06,1.35,.85,'#293d43')
        m.box(.2,2.7,0,.4,.4,.45,'#a3957f');m.box(.23,2.73,.45,.34,.34,.7,'#798c70')
        title='客餐厅 / 暖白 + 浅木';sub='对应首层西侧，净宽约 3.24 m；餐客厅连续布置'
        scale=135; center=(1070,770)
    elif kind=='bedroom':
        a,b=3.24,3.64;m.box(0,0,-.1,a,b,.1,'#b9a17d');m.box(0,0,0,a,.1,2.8,'#e4ded1');m.box(0,0,0,.1,b,2.8,'#e4ded1')
        m.box(.72,.2,0,1.5,2,.34,'#997956');m.box(.72,.2,.34,1.5,2,.22,'#ddd2ba');m.box(.72,.14,.1,1.5,.12,1.0,'#a88b66')
        m.box(.85,.35,.57,.55,.38,.12,'#f2ebdc');m.box(1.52,.35,.57,.55,.38,.12,'#f2ebdc')
        m.box(.72,1.2,.57,1.5,.9,.06,'#87978b')
        m.box(.16,.30,0,.43,.43,.5,'#b89b75');m.box(2.35,.30,0,.43,.43,.5,'#b89b75')
        m.box(.12,2.95,0,1.8,.6,2.4,'#d8ceba')
        for x in [.72,1.32]:m.box(x,3.556,.15,.018,.012,2.1,'#a3937c')
        title='老人房 / 温和照明与短动线';sub='对应首层东南房，净尺寸约 3.24 × 3.64 m；床宽 1.5 m'
        scale=180;center=(1000,880)
    else:
        a,b=3.24,3.16;m.box(0,0,-.1,a,b,.1,'#ccc8ba');m.box(0,0,0,a,.1,2.8,'#e6e4d9');m.box(0,0,0,.1,b,2.8,'#e6e4d9')
        m.box(.1,.1,0,3.0,.6,.82,'#a4ad9c');m.box(.1,.1,.82,3,.6,.05,'#eee9dd')
        m.box(.1,.7,0,.6,1.7,.82,'#a4ad9c');m.box(.1,.7,.82,.6,1.7,.05,'#eee9dd')
        m.box(.9,.21,.875,.72,.36,.02,'#798b8d');m.box(.15,1.30,.875,.48,.65,.03,'#36454a')
        m.box(.1,1.22,1.55,.55,.8,.18,'#657475');m.box(.1,1.4,1.73,.2,.4,1.07,'#657475')
        m.box(2.35,2.35,0,.7,.65,1.82,'#aeb8b2')
        m.box(.85,.1,1.6,2.1,.35,.75,'#c5cdbd')
        title='厨房 / L 型工作台';sub='对应首层西北厨房，净尺寸约 3.24 × 3.16 m；燃气厨房可关闭'
        scale=185;center=(1000,900)
    m.render(IMG/(kind+'.png'),title,sub,scale=scale,center=center)

for style in range(3): exterior(style)
for kind in ['living','bedroom','kitchen']: interior(kind)

pdf=canvas.Canvas(str(ROOT/'10x10三层住宅_方案与装修机电图册.pdf'),pagesize=(W,H))
pdf.setTitle('10×10m 三层农村住宅｜方案与装修机电图册')
pdf.setAuthor('住宅概念方案 / 2026-10-28')

def text(x,y,t,size=10,color=INK):
    t=t.replace('²','2')
    pdf.setFont('CN',size);pdf.setFillColor(HexColor(color));pdf.drawString(x,y,t)
def line(x1,y1,x2,y2,color=INK,width=1,dash=None):
    pdf.setStrokeColor(HexColor(color));pdf.setLineWidth(width);pdf.setDash(dash or []);pdf.line(x1,y1,x2,y2);pdf.setDash([])
def rect(x,y,w,h,fill=None,stroke=INK,width=1):
    pdf.setLineWidth(width);pdf.setStrokeColor(HexColor(stroke));pdf.setFillColor(HexColor(fill or '#ffffff'));pdf.rect(x,y,w,h,fill=bool(fill),stroke=bool(stroke))
def wrap(t,width,size=10):
    t=t.replace('²','2')
    out=[];s=''
    for ch in t:
        if pdfmetrics.stringWidth(s+ch,'CN',size)>width and ch not in '。，；：、）】%':
            out.append(s);s=ch
        else:s+=ch
    if s:out.append(s)
    return out
def para(x,y,t,width=490,size=11,leading=19,color=INK):
    for row in wrap(t,width,size):text(x,y,row,size,color);y-=leading
    return y
def panel(x,y,title,items,width=475):
    text(x,y,title,14,TEAL);line(x,y-10,x+width,y-10,'#bfd0cc',.7);y-=32
    for t in items:y=para(x,y,t,width,10.7,18)-12
    return y
def new(code,title,sub=''):
    pages.append({'code':code,'title':title})
    rect(0,0,W,H,'#ffffff','#ffffff')
    rect(0,H-13,W,13,TEAL,TEAL)
    text(42,H-52,code+'  /  '+title,24)
    text(44,H-78,sub,10,MUTED)
    line(42,55,W-42,55,'#bdccc9',.8)
    text(44,34,'10 × 10 m · 南向入户 · 概念深化 / 非施工图 · 2026.10.28',9,MUTED)
    text(W-187,34,f'{len(pages):02d}  /  {code}',9,MUTED)
def end():pdf.showPage()
def p(x,y):return OX+x*S,OY-y*S
def wl(a,b,c=INK,w=1,dash=None):line(*p(*a),*p(*b),c,w,dash)
def wr(x,y,w,h,fill=None,stroke=INK,lw=.6):
    xx,yy=p(x,y+h);rect(xx,yy,w*S,h*S,fill,stroke,lw)
def label(x,y,t,size=10,color=INK,center=True):
    xx,yy=p(x,y);pdf.setFont('CN',size);pdf.setFillColor(HexColor(color))
    (pdf.drawCentredString if center else pdf.drawString)(xx,yy,t)
def wall(a,b,width=.12):wl(a,b,INK,width*S)
def door(x,y,w=.9,orient='h',swing=1):
    if orient=='h':
        wl((x,y),(x+w,y),'#ffffff',.15*S);wl((x,y),(x,y+swing*w),MUTED,.7)
        xx,yy=p(x,y);pdf.setStrokeColor(HexColor('#a7b2b0'));pdf.setLineWidth(.5)
        if swing==1:pdf.arc(xx-w*S,yy-w*S,xx+w*S,yy+w*S,270,90)
        else:pdf.arc(xx-w*S,yy-w*S,xx+w*S,yy+w*S,0,90)
    else:
        wl((x,y),(x,y+w),'#ffffff',.15*S);wl((x,y),(x+swing*w,y),MUTED,.7)
        xx,yy=p(x,y);pdf.setStrokeColor(HexColor('#a7b2b0'));pdf.setLineWidth(.5)
        if swing==1:pdf.arc(xx-w*S,yy-w*S,xx+w*S,yy+w*S,270,90)
        else:pdf.arc(xx-w*S,yy-w*S,xx+w*S,yy+w*S,180,90)
def window(x,y,w,orient='h'):
    if orient=='h':
        wl((x,y),(x+w,y),'#ffffff',.245*S)
        for d in [-.07,0,.07]:wl((x,y+d),(x+w,y+d),'#5795a1',.7)
    else:
        wl((x,y),(x,y+w),'#ffffff',.245*S)
        for d in [-.07,0,.07]:wl((x+d,y),(x+d,y+w),'#5795a1',.7)
def sliding(x,y,w):
    wl((x,y),(x+w,y),'#ffffff',.15*S)
    wl((x,y-.025),(x+w*.58,y-.025),MUTED,.8)
    wl((x+w*.42,y+.025),(x+w,y+.025),MUTED,.8)
def sliding_v(x,y,w):
    wl((x,y),(x,y+w),'#ffffff',.15*S)
    wl((x-.025,y),(x-.025,y+w*.58),MUTED,.8)
    wl((x+.025,y+w*.42),(x+.025,y+w),MUTED,.8)
def mainentry():
    wl((4.05,9.88),(5.55,9.88),'#ffffff',.25*S)
    door(4.05,9.88,.75,'h',-1)
    wl((5.55,9.88),(5.55,9.13),MUTED,.7)
def dim(a,b,txt,offset=.45):
    x1,y1=a;x2,y2=b
    if abs(y1-y2)<.001:
        y=y1+offset;wl((x1,y),(x2,y),MUTED,.5)
        for x in [x1,x2]:wl((x,y-.10),(x,y+.10),MUTED,.7);wl((x,y1),(x,y),MUTED,.3)
        label((x1+x2)/2,y-.1,txt,8,MUTED)
    else:
        x=x1+offset;wl((x,y1),(x,y2),MUTED,.5)
        for y in [y1,y2]:wl((x-.10,y),(x+.10,y),MUTED,.7);wl((x1,y),(x,y),MUTED,.3)
        xx,yy=p(x-.12,(y1+y2)/2);pdf.saveState();pdf.translate(xx,yy);pdf.rotate(90);text(0,0,txt,8,MUTED);pdf.restoreState()
def symbol(x,y,t,color):
    xx,yy=p(x,y);pdf.setFillColor(white);pdf.setStrokeColor(HexColor(color));pdf.setLineWidth(1);pdf.circle(xx,yy,8,fill=1,stroke=1)
    pdf.setFont('CN',7);pdf.setFillColor(HexColor(color));pdf.drawCentredString(xx,yy-2.4,t)
def route(pts,color,width=1.5,dash=None):
    for a,b in zip(pts,pts[1:]):wl(a,b,color,width,dash)
def bed(x,y,w=1.5,h=2):
    wr(x,y,w,h,'#e7e0d3','#ae9c83');wr(x+.06,y+.09,w-.12,.35,'#faf8f1','#ae9c83');wl((x,y+.55),(x+w,y+.55),'#ae9c83',.6)
def stair(f=1):
    wr(3.72,.24,2.56,4.56,'#f1f3f1','#a5b1ad')
    for x in [3.72,5.13]:
        for i in range(10):wl((x,1.24+i*.28),(x+1.15,1.24+i*.28),'#8a9995',.6)
    pts=[(4.30,4.15),(4.30,.78),(5.7,.78),(5.7,4.15)]
    route(pts if f<3 else pts[::-1],'#718782',.7)
    tip=5.7 if f<3 else 4.30
    wl((tip,4.15),(tip-.11,3.94),'#718782',.7);wl((tip,4.15),(tip+.11,3.94),'#718782',.7)
    label(5,4.52,{1:'双跑楼梯 / 上至2F',2:'上至3F / 下至1F',3:'双跑楼梯 / 下至2F'}[f],8)
def furniture(f):
    if f==1:
        wr(.24,.24,3.24,.6,'#dce5dd','#7e9686');wr(.24,.84,.6,1.75,'#dce5dd','#7e9686')
        wr(1.05,.34,.7,.40,'#ffffff','#7e9686');wr(.34,1.4,.4,.65,'#a8b7aa','#7e9686')
        wr(2.55,2.54,.7,.65,'#dce5dd','#7e9686');label(2.90,2.94,'冰箱',6)
        wr(.8,3.95,1.6,.8,'#e8dfcf','#a69479')
        for xx in [.85,1.85]:
            for yy in [3.55,4.85]:wr(xx,yy,.45,.38,'#f1eade','#a69479')
        wr(.35,6.65,.8,2.2,'#e2d8c6','#a69479');wr(1.5,7.3,.6,1.0,'#e2d8c6','#a69479');wr(3.12,6.8,.28,1.8,'#bba98e','#a69479')
        wr(5.90,8.5,.35,1.05,'#e3dcca','#a69479')
    elif f==2:
        bed(.95,.65);wr(.35,3.95,1.6,.6,'#ddd4c1','#a69479');bed(.95,6.48);wr(.35,9.1,1.8,.6,'#ddd4c1','#a69479')
        wr(3.85,6.65,.7,1.8,'#e2d8c6','#a69479');wr(5.8,6.8,.3,1.5,'#bba98e','#a69479')
    else:
        wr(.4,.5,2.5,.35,'#ddd4c1','#a69479');wr(.55,2.1,1.6,.7,'#e8dfcf','#a69479');wr(.6,3.65,2.0,.8,'#e2d8c6','#a69479')
        wr(.65,7.15,1.25,.7,'#e6dfca','#a69479');wr(.3,8.9,2.5,.5,'#e0e8d4','#9aaa82')
        wr(3.85,6.65,.7,1.8,'#e2d8c6','#a69479')
    bed(7.22,6.45);wr(6.72,9.10,1.8,.6,'#ddd4c1','#a69479')
    # Stacked bathroom fixtures.
    wr(7.70,.24,.95,.95,'#e1eef0','#7d9ba0');wl((7.70,.24),(8.65,1.19),'#7d9ba0',.6)
    wr(9.02,.50,.50,.72,'#ffffff','#7d9ba0');wr(8.9,2.32,.72,.45,'#ffffff','#7d9ba0')
    wr(8.9,3.30,.6,.6,'#e1eef0','#7d9ba0');wr(7.85,4.10,.7,.5,'#e1eef0','#7d9ba0')

def baseplan(f,labels=True,furn=True,dims=True):
    wr(0,0,10,10,'#fbfaf5','#ffffff')
    wr(7.7,.24,2.06,2.64,'#edf4f4','#ffffff');wr(7.7,3.12,2.06,1.68,'#edf4f4','#ffffff')
    if f==3:wr(.24,6.12,3.24,3.64,'#eef1e4','#ffffff')
    # External wall centerline offset preserves 10x10 outer envelope.
    for a,b in [((.12,.12),(9.88,.12)),((9.88,.12),(9.88,9.88)),((9.88,9.88),(.12,9.88)),((.12,9.88),(.12,.12))]:wall(a,b,.24)
    # Longitudinal partitions; all are indicative, not structural walls.
    wall((3.6,.24),(3.6,9.76),.24);wall((6.4,.24),(6.4,9.76),.24)
    wall((7.64,.24),(7.64,4.86));wall((7.7,3.0),(9.76,3.0),.24);wall((6.46,4.86),(9.76,4.86))
    wall((6.46,6.06),(9.76,6.06))
    if f==1:wall((.24,3.46),(3.54,3.46))
    else:
        wall((.24,4.86),(3.54,4.86));wall((.24,6.0 if f==3 else 6.06),(3.54,6.0 if f==3 else 6.06),.24 if f==3 else .12)
    # Circulation: cross corridor links west rooms / stair / east service passage.
    for xx in [3.6,6.4]:wl((xx,4.92),(xx,6.0),'#ffffff',.26*S)
    wl((3.72,4.8),(6.28,4.8),'#ffffff',.15*S)
    if f==1:
        sliding(2.0,3.46,1.05);wl((3.6,8.65),(3.6,9.60),'#ffffff',.26*S)
        mainentry();label(4.8,10.25,'南向主入口',9,TEAL)
    else:
        door(2.0,4.86,.95,'h',-1)
        if f==2:door(2.50,6.06,.88,'h',1)
        else:window(.8,6.0,2.1);wl((3.6,7.15),(3.6,8.10),'#ffffff',.26*S);door(3.6,7.15,.95,'v',-1)
    door(6.63,4.86,.88,'h',-1)
    sliding_v(7.64,1.65,.8);sliding_v(7.64,3.65,.8);door(8.75,6.06,.9,'h',1)
    for x,w in [(.75,2.15),(7.0,2.05)]:
        if not(f==3 and x<3):window(x,9.88,w)
    if f>1:window(4.05,9.88,1.75)
    window(.75,.12,2.15);window(4.1,.12,1.8)
    for y,w in [(1.0,1.1),(3.5,.85),(7.1,1.8)]:window(9.88,y,w,'v')
    if f<3:window(.12,7.1,1.8,'v')
    stair(f)
    if furn:furniture(f)
    if labels:
        if f==1:
            roomtexts=[(1.85,1.55,'厨房','3.24 × 3.16 m'),(1.85,5.6,'餐厅 / 连通客厅','西侧连续净宽 3.24 m'),(1.85,9.4,'客厅','约 12㎡起居区'),(4.95,8.85,'玄关 / 茶座','主入口宽 1.50 m')]
        elif f==2:
            roomtexts=[(1.85,3.15,'卧室 02','3.24 × 4.56 m'),(1.85,8.85,'卧室 03','3.24 × 3.64 m'),(4.95,9.15,'家庭起居','2.56 × 3.64 m')]
        else:
            roomtexts=[(1.85,3.3,'书房 / 多功能','3.24 × 4.56 m'),(1.85,8.4,'西南露台','净约 11.8㎡'),(4.95,9.15,'休闲厅','2.56 × 3.64 m')]
        roomtexts +=[(8.2,8.8,['','老人房 01','卧室 04','客房 05'][f],'3.24 × 3.64 m'),(8.8,1.7,'卫生间','2.06 × 2.64 m'),(8.7,4.20,'家务 / 洗衣','2.06 × 1.68 m')]
        for x,y,a,b in roomtexts:label(x,y,a,10);label(x,y+.28,b,7.5,MUTED)
        label(5.0,5.6,'交通厅 / 楼梯前室',8,MUTED);label(7.02,3.1,'过道',7,MUTED)
    if dims:
        dim((0,0),(10,0),'10000',-.95)
        for a,b,t in [(0,3.6,'3600'),(3.6,6.4,'2800'),(6.4,10,'3600')]:dim((a,0),(b,0),t,-.42)
        dim((0,0),(0,10),'10000',-.85)
        for a,b,t in [(0,4.86,'4860'),(4.86,6.06,'1200'),(6.06,10,'3940')]:dim((10,a),(10,b),t,.38)
    # North arrow and scale bar.
    xx,yy=p(10.9,-.15);line(xx,yy-25,xx,yy+5,TEAL,1.5);line(xx,yy+5,xx-5,yy-4,TEAL,1.5);line(xx,yy+5,xx+5,yy-4,TEAL,1.5);text(xx-4,yy+13,'N',10,TEAL)
    label(5,11.15,'南侧临路 / 室外用地与退界待实测',9,MUTED)
    xx,yy=p(0,11.2)
    for i in range(4):rect(xx+i*S/2,yy,S/2,5,INK if i%2==0 else '#ffffff',INK,.5)
    text(xx,yy-15,'0           1           2m   |   A3 原幅 1:60',8,MUTED)

def key(x,y,rows):
    for col,labelt in rows:
        line(x,y+3,x+27,y+3,col,2);text(x+38,y,labelt,10);y-=25
    return y

# 01 Cover
new('00','南院 · 三层乡居','10 × 10 m 农村自建房 | 空间方案、装修意向、水电网气路线')
pdf.drawImage(str(IMG/'01_现代简约.png'),40,125,width=710,height=533,mask='auto')
panel(785,670,'项目基线',[
'已确认：南侧临路、南向入户。建筑外包尺寸 10,000 × 10,000 mm，三层。',
'暂按 5–6 人、5 卧室 + 书房；首层设老人房。三层西南角设置露台。',
'主方案：现代简约。附新中式、乡村坡屋顶两种外观意向。',
'本册属于方案深化，可供家庭讨论和建筑、结构、机电专业接续设计；不具备直接施工条件。'],width=355)
panel(785,330,'面积与标高',[
'首层约 100㎡；二层约 100㎡。',
'三层围护区域外包投影约 85.6㎡，露台占位约 14.4㎡（净约 11.8㎡）。合计围护投影约 285.6㎡；法定建筑面积另核。',
'首层层高 3.60m；二、三层各 3.30m；屋面 +10.20m；主方案女儿墙顶 +11.30m。'],width=355)
end()

new('A-00','设计条件与备选方案','设计依据为用户提供的尺寸及南向入户条件；其余均为明确假设')
panel(48,700,'空间组织',[
'1F：西北可关闭厨房，西侧餐客厅，东南老人房，东北卫生间及洗衣；中部双跑楼梯和玄关。',
'2F：西北、南西、南东三卧室；中南家庭起居；东北卫生间与家务空间。',
'3F：西北书房，东南客房，东北卫生间与家务空间；西南露台，中南休闲厅。',
'厨卫沿外墙布置，卫生间上下叠合。楼梯间采光由北窗承担；各层卧室均有直接外窗。',
'外墙和两道纵向主分隔暂按240mm，一般内隔墙120mm，卫浴与洗衣间分隔240mm；墙厚不表示承重性质。未布置结构柱，净尺寸须再核。',
'南侧道路位置已确认；室外水表、电表、燃气表、污水与雨水接驳点均未确认。'],width=495)
panel(622,700,'三个外观选项',[
'A 现代简约：暖白外墙、灰色窗框、少量木色或金属饰面；平屋面外观，采用本册平立剖方案。',
'B 新中式：同一基本体量，深色腰线和格栅；构造突出部不得越界，饰面及附属构件需验算固定。',
'C 乡村坡屋顶：后部增加坡屋顶意向，屋脊约+12.00m；需重新校核限高、风雪荷载、排水与屋架。此选项不与A方案屋面详图混用。',
'未确认事项：城市/县镇、地形高差、朝向偏角、四侧退界、相邻房屋、地勘、抗震设防、供电容量、用水压力、气源、预算和地方审批要求。',
'本册不含：基础和配筋、结构计算、最终设备选型、施工节点详图、工程量清单、消防与节能合规审查。'],width=495)
text(48,136,'图册阅读顺序：A 空间建筑 → P 给排水 → E 强电 → N 网络 → G 燃气 → I 装修 → V 效果 → X 复核清单',11,TEAL)
end()

plan_notes={1:[
'西侧厨房净约10.2㎡，餐客厅贯通；厨房开口1.05m，建议可关闭移门或外开门，最终随燃气要求确定。',
'老人房床1500×2000mm；床侧通道目标≥600mm。卫生间位于同层北侧，尚非完整无障碍套间。',
'东北服务过道净约1.06m；中部交通带净约1.08m。门扇、扶手、结构柱不得进一步侵占有效通行宽度。',
'入口1.50m；卧室门洞暂0.90–0.95m；卫生间门洞0.80m，宜外开或移门并复核救援开启。',
'客厅南、西设窗；厨房北窗、卫生间东窗。仅示意开口位置，开启扇和防坠安全另深化。'],
2:[
'西北卧室约14.8㎡；两间南卧各约11.8㎡；家庭起居约9.3㎡，均为墙间估算，不含柱与饰面。',
'西北卧室从横向交通厅进入，南侧卧室从同一交通厅进入；卧室不作为穿越通道。',
'东北卫生间和洗衣区与首层对位；楼层电箱在公共交通区，弱电与强电分管布置。',
'净窗洞暂按南窗2.05–2.15m宽；窗台约0.85m、窗高约1.95m，实际需满足当地节能与安全规定。',
'空调采用分体机预留方案。室外机位置需结合外立面、检修面和邻居边界二次确认。'],
3:[
'东南客房约11.8㎡；西北书房约14.8㎡，可作多功能房，但不按新增常住卧室核算。',
'西南露台占位约3.60×4.00m；扣除围护后净约11.8㎡。通过中南休闲厅向西开门进入。',
'露台周边防护高度暂1.10m，仅作方案控制值；需按当地规定、可踏面和防攀爬要求确定。',
'露台地面低于室内的做法、门槛防水、排水坡与溢流一并深化；不建议自行降结构板。',
'主方案屋面不上人。屋面检修出入口或设备维护通道需专项安排，不在图中增设第四层楼梯间。']}
for f in [1,2,3]:
    new(f'A-0{f}',f'{f}F 家具与尺寸平面','尺寸单位 mm；外轮廓为墙外边线，分段尺寸至示意隔墙定位线；室内标注为估算净尺寸')
    baseplan(f)
    yy=panel(680,700,'空间与动线',plan_notes[f],width=458)
    panel(680,yy-5,'楼梯控制',[
    '梯间净宽约2.56m，分两跑各约1.15m，中间约0.26m。安装扶手后有效净宽须复核。',
    '每层暂设20级、每跑10个踢面和9个踏面；踏面280mm，单跑水平长2520mm；两端平台约1000/1040mm。',
    '1F→2F：20×180=3600mm；2F→3F：20×165=3300mm。梯梁、板厚及净空尚未验算。'],width=458)
    end()

# Roof plan: all boundaries coincide with third-floor envelope.
new('A-04','屋面与露台排水意向','主方案 A 平屋面；箭头为排水方向示意，不代表已经计算的找坡厚度')
wr(0,0,10,10,'#f6f5ef')
wr(0,6,3.6,4,'#e5eddf')
for a,b in [((0,0),(10,0)),((10,0),(10,10)),((10,10),(3.6,10)),((3.6,10),(3.6,6)),((3.6,6),(0,6)),((0,6),(0,0))]:wall(a,b,.18)
for pts in [[(4,2),(9.5,.5)],[(4,4),(9.5,.5)],[(6,7),(9.5,9.5)],[(1.8,7),(0.4,9.5)]]:
    route(pts,COL['R'],1.5);symbol(*pts[-1],'R',COL['R'])
label(5,2.6,'不上人屋面 +10.20',12);label(6.5,6.7,'找坡暂按1%–2%意向',10)
label(1.8,8.2,'三层露台 +6.90附近',9);label(1.8,8.6,'主排 + 独立溢流',9)
symbol(9.5,.5,'R1',COL['R']);symbol(9.5,9.5,'R2',COL['R']);symbol(.4,9.5,'R3',COL['R'])
dim((0,0),(10,0),'10000',-.55);dim((0,0),(0,10),'10000',-.55)
panel(680,700,'防水与排水原则',[
'R1、R2：屋面东侧两个候选雨水口及外立管位置；R3：露台西南候选雨水口。雨水管与污水管分开。',
'屋面管径、雨水口数量及排水能力须按当地暴雨强度、汇水面积和堵塞工况计算，图中未定型。',
'主排水口设置可清理格栅；露台另设向安全方向排放的可见溢流，溢流口高程须低于室内防水控制线。',
'屋面：结构板 → 找坡/保温系统 → 防水层 → 保护层。层次顺序与材料由当地节能、气候及选定系统确定。',
'女儿墙、管根、泛水、门槛及雨水口需节点详图；屋面所有设备底座需结构及防水配合，禁止后期随意打穿。',
'太阳能、光伏、水箱均未计入荷载。若增设，应先验算屋面荷载、抗风固定、防雷及检修通道。'],width=458)
end()

new('A-05','南立面与东立面','正投影示意；色彩对应 A 现代简约，立面洞口与平面主要开口对应')
def elevation(x0,y0,side):
    sc=36
    def rr(x,z,w,h,co):rect(x0+x*sc,y0+z*sc,w*sc,h*sc,co,INK,.5)
    rr(0,0,10,10.2,'#eeeae0')
    if side=='南':rr(0,6.9,3.6,3.3,'#ffffff');rr(0,6.9,3.6,1.1,'#d8d4c8')
    for z in [0,3.6,6.9]:
        if side=='南':
            if z<6.9:rr(.75,z+.85,2.15,1.95,'#b6d0d5')
            rr(7,z+.85,2.05,1.95,'#b6d0d5');rr(4.05,z+.85,1.75,1.95,'#b6d0d5')
        else:
            for x,w,zz,h in [(1,1.1,1.6,.75),(3.5,.85,1.15,1.15),(7.1,1.8,.85,1.95)]:rr(x,z+zz,w,h,'#b6d0d5')
    if side=='南':rr(4.05,0,1.5,2.65,'#637e84');rr(6.25,.5,.28,9.45,'#a88a67')
    rr(3.6 if side=='南' else 0,10.2,6.4 if side=='南' else 10,1.1,'#e7e2d7')
    for z,t in [(0,'±0.000'),(3.6,'+3.600'),(6.9,'+6.900'),(10.2,'+10.200'),(11.3,'+11.300')]:
        line(x0-12,y0+z*sc,x0+370,y0+z*sc,'#b7c3c0',.4,[2,3]);text(x0+375,y0+z*sc-3,t,8,MUTED)
    text(x0+120,y0-27,side+'立面 / 示意',13,TEAL)
elevation(95,220,'南');elevation(655,220,'东')
para(48,132,'窗台与窗高按方案表达；防护、开启方式、遮阳、窗墙比、保温及抗风压需结合地区深化。立面无结构柱、梁配筋信息。东侧室外机、雨水管和污水管宜集中整合并保留检修通道。',1085,11,19)
end()

new('A-06','楼梯剖面与层高','沿中部楼梯的展开控制示意；两跑投影为展开表达，并非施工剖面')
x0,y0,sc=125,210,42
for z,tt in [(0,'1F ±0.000'),(3.6,'2F +3.600'),(6.9,'3F +6.900'),(10.2,'屋面 +10.200')]:
    rect(x0,y0+z*sc,420,7,'#667c7b','#667c7b');text(x0+440,y0+z*sc,tt,10)
for base,rise in [(0,.18),(3.6,.165)]:
    for n in range(10):
        xa=x0+30+n*.28*sc;za=y0+(base+(n+1)*rise)*sc
        line(xa,za,xa+.28*sc,za,INK,1.6);line(xa,za-rise*sc,xa,za,INK,1.0)
    zmid=base+10*rise;line(x0+156,y0+zmid*sc,x0+210,y0+zmid*sc,INK,2)
    for n in range(10):
        xa=x0+210+n*.28*sc;za=y0+(zmid+(n+1)*rise)*sc
        line(xa,za,xa+.28*sc,za,INK,1.6);line(xa,za-rise*sc,xa,za,INK,1.0)
text(135,160,'展开表达：平台 + 第一跑 + 中间平台 + 第二跑 + 平台',10,MUTED)
panel(735,700,'楼梯与结构交接',[
'楼梯净平面约2.56×4.56m。两端平台约1.00m和1.04m；单跑宽约1.15m、9个踏面×0.28m。',
'首层20个踢面×0.180m = 3.600m；二层20个踢面×0.165m = 3.300m。图示步数为方案控制，铺装完成面须统一计算。',
'踏步上方净高、平台梁下净高、扶手和栏杆均待剖面碰撞检查；目标净空按适用规范确定，不能仅依平面判断。',
'建议由当地设计单位结合抗震与地勘选择结构体系。图中未指定砖混、框架或构造柱，不得根据墙线推定承重。',
'禁止在梁柱、楼板和楼梯承重构件上任意开槽开孔；管线洞口须在结构图中预留并经专业确认。'],width=402)
end()

# Plumbing plans
def plumbing(f):
    baseplan(f,False,True)
    # Separate potable riser and drainage stack along east facade; show schematic routing.
    route([(9.60,4.5),(9.60,1.35),(8.20,1.35),(8.20,.78)],COL['C'])
    route([(9.60,2.55),(9.25,2.55)],COL['C']);route([(9.60,1.35),(9.25,.86)],COL['C'])
    route([(9.60,4.5),(9.2,3.6)],COL['C']);route([(9.60,4.5),(8.2,4.35)],COL['C'])
    route([(9.35,4.5),(9.35,1.50),(8.35,1.50),(8.35,.78)],COL['H'],1.4,[5,2])
    route([(9.35,2.7),(9.1,2.7)],COL['H'],1.4,[5,2])
    route([(9.35,4.5),(8.3,4.5)],COL['H'],1.4,[5,2])
    for pts in [[(8.15,.75),(8.15,1.1),(9.85,1.1)],[(9.25,.85),(9.85,.85)],[(9.2,2.55),(9.85,2.55),(9.85,1.1)],[(9.2,3.6),(9.85,3.6),(9.85,1.1)],[(8.2,4.3),(9.85,4.3),(9.85,3.6)]]:route(pts,COL['D'],1.4)
    if f==1:
        route([(9.60,4.5),(9.6,5.5),(2.9,5.5),(2.9,2.85),(1.4,2.85),(1.4,.55)],COL['C'],1.5)
        route([(9.35,4.5),(9.35,5.65),(2.75,5.65),(2.75,3.0),(1.55,3),(1.55,.55)],COL['H'],1.4,[5,2])
        route([(1.4,.55),(.15,.55),(.15,10.4)],COL['D'],1.6)
        symbol(.15,.55,'K',COL['D']);label(.65,10.65,'厨房独立排出',7,COL['D'])
        route([(9.60,5.5),(10.7,5.5),(10.7,10.5)],COL['C'],1.6)
        label(10.7,10.9,'水表方向',7,COL['C'])
    symbol(9.6,4.5,'C',COL['C']);symbol(9.35,4.1,'H',COL['H']);symbol(9.85,1.1,'D1',COL['D'])
    for x,y in [(8.0,.9),(8.45,2.75),(8.5,3.8)]:symbol(x,y,'FD',COL['D'])
    if f==3:symbol(.40,9.5,'R3',COL['R']);route([(2.6,7.6),(.4,9.5)],COL['R'])

for f in [1,2,3]:
    new(f'P-0{f}',f'{f}F 给水、热水与排水路线','线路在平面上的偏移仅为读图；需分别确定吊顶、管井、墙面或地面敷设标高')
    plumbing(f)
    yy=key(680,700,[(COL['C'],'C / 蓝实线：冷水'),(COL['H'],'H / 红虚线：热水'),(COL['D'],'D / 棕实线：污废水；FD：地漏'),(COL['R'],'R / 绿线：雨水，独立系统')])
    yy=panel(680,yy-15,'布置与规格复核起点',[
'C给水立管：候选公称DN25；入户候选DN32；户内干管候选DN20、单点支管候选DN15。热水干管候选DN20。均需按水压和同时用水量核算。',
'公称DN不等于塑料管外径；不得直接据此购买De规格。材料、壁厚、温压等级与连接方式由给排水专业确定。',
'污水立管D1：候选DN100（常见塑料外径110须再核）；坐便支管同级。台盆/淋浴/洗衣候选DN50；厨房独立废水管候选DN75。',
'排水横管坡向立管或室外检查井；坡度须按管材、管径、流量计算，意向控制约1%–2%，不得用本图替代标高设计。',
'地漏设水封并便于补水；洗衣机采用专用防返溢接口。污水横管转弯、立管底部和检修节点设置清扫/检修条件。'],width=458)
    end()

new('P-04','给排水系统与室外衔接','生活热水暂按空气源热泵集中供热；设备位置、容量、循环和结构荷载待确认')
for yy,tt in [(260,'1F'),(430,'2F'),(590,'3F'),(690,'屋面')]:line(70,yy,690,yy,'#c3d0cc',.7);text(75,yy+10,tt,11,TEAL)
for xx,co,t in [(220,COL['C'],'C 冷水'),(310,COL['H'],'H 热水'),(530,COL['D'],'D1 污水通气')]:
    line(xx,190,xx,700,co,3);text(xx-28,720,t,10,co)
for yy in [280,450,610]:
    for xx,co,dy in [(220,COL['C'],0),(310,COL['H'],-12)]:line(xx,yy+dy,400,yy+dy,co,1.4)
    line(430,yy-35,530,yy-35,COL['D'],1.8);text(405,yy+15,'各层用水点',9)
line(110,190,220,190,COL['C'],2);text(80,165,'水表→过滤→总阀→防回流（按供水要求）',9)
line(310,190,400,190,COL['H'],2);rect(350,105,210,55,PALE,TEAL);text(366,137,'地面设备位：空气源热泵',10);text(366,119,'储水量 / 水压 / 用电待算',9)
line(400,160,400,190,COL['H'],1.5)
line(220,190,220,130,COL['C'],1.5);line(220,130,350,130,COL['C'],1.5)
line(530,190,650,190,COL['D'],2);text(570,165,'检查井→合规污水系统',9)
panel(735,700,'系统说明',[
'给水从南侧室外候选表位进入，沿公共区吊顶至东北给水立管；各层设置分区阀，洁具前设角阀。',
'热水由地面室外候选设备区供应，立管与热水横管保温；是否设回水循环取决于最远点等待时间。图中未绘制回水管，不得将冷水管当作回水。',
'立管D1延伸至屋面通气，终端高度、与门窗/新风口距离按规范复核；通气立管不得接雨水或厨房排烟。',
'卫生间排水需确定同层或异层排水方式及结构预留。当前路线为拓扑示意，穿板孔和吊顶净高尚未设计。',
'室外雨污分流；无市政污水时需由当地专业单位确定化粪池/处理设施容量、位置、防渗、清掏和与水井的间距。图中不预设化粪池位置。',
'完工应进行给水压力与冲洗试验、排水通水试验、防水闭水试验，并留存隐蔽影像和实测竣工图。'],width=402)
end()

# Electrical combined lighting/power, individual circuits identified in notes.
lights={1:[(1.8,1.8),(1.8,4.4),(1.8,7.8),(5.0,7.8),(5,5.45),(8.2,7.8),(8.6,1.8),(8.7,4.1),(5,1)],2:[(1.8,2.8),(1.8,7.8),(5,7.8),(5,5.45),(8.2,7.8),(8.6,1.8),(8.7,4.1),(5,1)],3:[(1.8,2.8),(1.8,7.8),(5,7.8),(5,5.45),(8.2,7.8),(8.6,1.8),(8.7,4.1),(5,1)]}
outlets={1:[(.4,7.2),(3.3,7.3),(4.0,8.6),(6.7,7.0),(9.5,7.0),(1.8,.9),(.9,2.2),(3.1,2.8),(8.9,3.8),(8.9,2.7)],2:[(.4,1.8),(3.3,2),(1.9,4.4),(.4,7.1),(3.3,7.1),(5.9,8.1),(6.7,7),(9.5,7),(8.9,3.8)],3:[(.4,2.0),(2.5,2.7),(1.9,4.4),(5.9,8.1),(6.7,7),(9.5,7),(8.9,3.8)]}
def electrical(f):
    baseplan(f,False,False)
    # Corridor trunk with branches routed orthogonally; separate branch identities in schedule.
    route([(6.15,5.5),(.7,5.5)],COL['E'],2)
    route([(6.15,5.5),(9.3,5.5)],COL['E'],2)
    for x,y in outlets[f]:
        route([(x,5.5),(x,y)],COL['E'],.8,[2,2]);symbol(x,y,'SO',COL['E'])
    for x,y in lights[f]:
        route([(5.75,5.7),(x,5.7),(x,y)],COL['L'],.65,[4,3]);symbol(x,y,'L',COL['L'])
    for x,y in [(2.9,5.05),(9.4,6.35),(7.8,1.45),(5.7,9.45)]:symbol(x,y,'S',COL['L'])
    for x,y in ([(.45,8.7),(9.5,8.7)] if f==1 else[(.45,1.4),(9.5,8.7)]+([(.45,8.7)] if f==2 else [])):
        symbol(x,y,'AC',COL['E']);route([(x,y),(x,5.5),(6.15,5.5)],COL['E'],.9,[7,2])
    route([(6.15,5.5),(6.15,6.45),(6.28,6.45)],COL['E'],1.6)
    symbol(6.28,6.45,'DB',COL['E']);label(5.0,6.4,f'DB{f} 公共区配电箱',8,COL['E'])

for f in [1,2,3]:
    new(f'E-0{f}',f'{f}F 强电、照明与开关点位','分色表达功能，线条不代表导线数量；最终回路和保护整定以电气设计为准')
    electrical(f)
    yy=key(680,700,[(COL['E'],'SO：插座；AC：空调专用；DB：楼层箱'),(COL['L'],'L：灯具；S：开关；黄虚线：照明通路')])
    panel(680,yy-10,'线路与安装意向',[
'楼层箱位于交通厅东侧墙面，保持干燥可检修；总箱与表箱位置待供电条件确认。强电干线沿公共区吊顶/专用竖向路由敷设。',
'照明、普通插座、厨房台面、冰箱、洗衣、空调、热水设备分别考虑独立回路；图中共享路径不表示共用一条回路。',
'照明候选铜芯1.5mm²；普通插座候选2.5mm²；厨房/空调2.5–4mm²；大功率设备4–6mm²仅为估算起点。穿管成束、距离和温度均影响载流量。',
'候选面板中心高：普通插座0.30m；开关1.10m；厨房台面插座1.15m左右（先定台面）；空调2.20m附近。均相对完成地面。',
'卫生间插座需避开淋浴禁设区并满足适用分区、防护等级和等电位要求；本图点位需结合最终洁具、隔断和防溅范围移位。',
'楼梯和玄关建议双控/感应；老人房增设床边夜灯、床头双控。探测器位置另按消防要求设计。'],width=458)
    end()

new('E-04','配电架构与回路表','只提供逻辑框架；入户容量、相制、断路器、线径和接地型式均须专业计算')
boxes=[(65,600,190,65,'供电表箱 / 电源条件待核'),(330,600,190,65,'MDB 总配电箱'),(630,635,180,55,'DB1 首层'),(630,525,180,55,'DB2 二层'),(630,415,180,55,'DB3 三层'),(330,330,190,65,'热泵 / 室外设备专用')]
for x,y,w,h,t in boxes:rect(x,y,w,h,PALE,TEAL);para(x+12,y+h/2+2,t,w-24,11,16)
line(255,632,330,632,COL['E'],2)
for y in [662,552,442]:line(520,632,575,632,COL['E'],2);line(575,632,575,y,COL['E'],2);line(575,y,630,y,COL['E'],2)
line(425,600,425,395,COL['E'],2)
panel(850,700,'保护与接地',[
'进线总开关、浪涌保护、隔离及支路保护应协调配合。终端漏电保护灵敏度/动作时间需按适用规范与设备类型选择。',
'以常见30mA附加人身保护作为终端复核起点，不统一替代专业选择；避免全屋仅设一个漏保。',
'PE保护导体连续可靠，不用水管或燃气管作接地体。接地型式随供电系统确定。',
'总等电位、卫浴局部等电位、防雷和接地电阻目标需专项设计。'],width=290)
rows=[('照明','各层分区','铜1.5mm²候选','功率/长度/压降'),('普通插座','各层独立','铜2.5mm²候选','回路点数/同时率'),('厨房/洗衣','按设备分路','铜2.5–4mm²候选','额定功率/专线'),('分体空调','建议每机专线','铜2.5–4mm²候选','启动/变频/距离'),('热泵/预留充电','独立计算','不预先定型','三相条件/容量/距离')]
x=[65,245,445,675];yy=255
for a,b,c,d in [('类别','回路原则','候选线径','必须复核项')]+rows:
    rect(60,yy-9,750,30,'#f1f5f3' if yy==255 else '#ffffff','#ccd7d3',.4)
    for xx,tt in zip(x,[a,b,c,d]):text(xx+6,yy,tt,9)
    yy-=30
end()

def networking(f):
    baseplan(f,False,False)
    origin=(6.08,5.25)
    points=[(5.0,5.25,'AP'),(8.8,8.85,'RJ')]
    if f==1:points +=[(3.1,7.1,'TV'),(4.8,9.6,'IC'),(.3,9.5,'CAM')]
    elif f==2:points +=[(1.8,3.8,'RJ'),(1.8,8.85,'RJ'),(5.8,8.1,'TV')]
    else:points +=[(1.8,2.5,'RJ'),(5.8,8.1,'TV'),(3.3,9.5,'CAM')]
    for x,y,t in points:
        route([origin,(x,5.25),(x,y)],COL['N'],1.2,[4,2]);symbol(x,y,t,COL['N'])
    symbol(*origin,'IT',COL['N']);label(5.0,6.38,'每点独立回主机柜 / 星形布线',8,COL['N'])

for f in [1,2,3]:
    new(f'N-0{f}',f'{f}F 网络、电视与安防预留','无线覆盖为候选点位；结构和建成环境会影响信号，交付前应实测调整')
    networking(f)
    yy=key(680,700,[(COL['N'],'IT：弱电竖向通路；AP：吸顶无线'),(COL['N'],'RJ：网络面板；TV：电视网络；IC：门口对讲'),(COL['N'],'CAM：有线摄像头预留（PoE候选）')])
    panel(680,yy-10,'布线与设备意向',[
'首层交通区设置通风弱电柜（不在密闭楼梯踏步空腔内）：光纤终端 → 路由器 → PoE交换机 → 各层AP/网口/摄像头。配独立电源并留UPS空间。',
'每个网口使用独立六类铜缆回到主机柜；电视、书桌建议双网口。层间使用独立弱电管路，预留光纤和牵引线。',
'水平永久链路控制在90m以内，整条通道按100m边界复核；超距改光纤。禁止串接面板形成链式布线。',
'强弱电分管分盒；并行间距、交叉处理及防雷隔离按规范和厂家要求确定，交叉尽量正交。各防火分隔处做相应封堵。',
'室外摄像头、AP和对讲线缆需满足防水、防紫外和浪涌防护；摄像方向仅覆盖自家入口和院内。',
'编号建议：F1-AP01、F2-RJ01等，端口两端同标；验收测通断、线序与链路性能并交付端口表。'],width=458)
    end()

new('G-01','燃气路线与厨房安全布置','气源未确认：仅画天然气条件预留；燃气方案须由当地燃气经营单位设计、安装、验收')
baseplan(1,False,True)
route([(-.55,10.4),(-.55,2.05),(.30,2.05),(.55,1.75)],COL['G'],2.5)
symbol(-.55,9.65,'GM',COL['G']);symbol(-.55,2.05,'V',COL['G']);symbol(.55,1.75,'G',COL['G'])
label(1.7,1.6,'燃气灶候选',9,COL['G']);label(-.55,10.8,'外墙表位待燃气公司定',7,COL['G'])
route([(.55,1.75),(.15,1.75),(-.4,1.75)],'#708181',1.5,[3,2])
panel(680,700,'天然气条件预留',[
'候选路径：南侧室外接入 → 西外墙可检修表位/阀门 → 沿西外墙至西北厨房 → 就近穿外墙 → 灶前阀 → 合规连接件 → 灶具。',
'只允许在气源、外墙可使用条件和接驳位置确认后深化。图示室外管线可能涉及退界，不能据此占用邻地或公共道路。',
'室内管线保持可检查，不经过卧室、卫生间、封闭楼梯间或其他禁设部位；不埋入结构，不与电线共管。',
'厨房应可关闭且有直接对外通风；灶具与窗帘、插座、燃物、其他管线间距依当地要求和设备说明确定，图中未给出虚构固定距离。',
'气体报警器及自动切断装置按当地要求配置。天然气探测器与液化气探测器安装位置不同，须按气种和厂家安装图确定。',
'本方案热水采用电驱空气源热泵意向，不预设燃气热水器或烟道。若改燃气热水器，应专项设计供气能力及独立安全排烟。'],width=458)
panel(680,230,'若采用瓶装液化气',[
'不得直接套用本图天然气表位和路线；需由当地合规供应单位确定钢瓶安放、通风、防火、调压器及连接方式。未确认气源前不采购燃气设备。'],width=458)
end()

new('I-01','客餐厅、卧室装修设计','以低维护、暖色照明和老人易用为目标；家具尺寸与平面对应')
pdf.drawImage(str(IMG/'living.png'),45,300,width=585,height=439)
panel(680,700,'客餐厅',[
'地面：浅暖灰哑光砖或耐磨地板；客餐厅同材连续铺设。铺装分格先对齐门口与家具，避免窄条收边。',
'墙面：暖白耐擦洗涂料；电视墙采用平整基层加少量木色饰面，墙上设备固定需核实基层。',
'顶面：以平顶或小范围边吊为主；先排定横向水电管线与空调再确定吊顶高度。',
'家具：三人沙发约2200×800，茶几约1000×600；餐桌约1600×800。净宽约3240mm，选小进深家具。',
'灯光：客餐厅3000–3500K、显色Ra≥90作为选型目标；餐桌吊灯避免直视眩光；照度需按实际灯具计算。'],width=458)
panel(48,260,'老人房 / 标准卧室',[
'首层床1500×2000mm；床头两侧配置触手可及开关，夜间下床路径设置低亮度照明。柜深600mm，优先推拉门或核对柜门与床的距离。',
'墙面低反光暖白，床头局部浅木或织物质感；选择可清洁、环保达标材料。窗帘双层，避免落地轨道或线缆形成绊倒点。',
'完成面高差尽量少；门槛、家具圆角、扶手需求结合老人活动能力再定。本方案尚未达到轮椅无障碍住宅设计深度。'],width=1090)
end()

new('I-02','厨房、卫生间与露台装修节点','节点是构造层次与控制事项，不替代选定系统的材料厚度及施工详图')
pdf.drawImage(str(IMG/'kitchen.png'),45,300,width=585,height=439)
panel(680,700,'厨房与卫生间',[
'厨房L型柜：台面暂高850mm、深600mm；水槽在北台面，灶具在西台面，冰箱靠东南角。安装高度按使用者和设备调整。',
'厨房地面防滑易清洁；燃气管和阀门保持可检查。油烟机独立排烟至室外合规位置，不接卫生间排风或雨污管。',
'卫生间约2060×2640mm：西北约950×950淋浴区，东北坐便，东南台盆；门宜外开或移门，避免堵住内部救援。',
'卫生间地面坡向地漏，淋浴区玻璃隔断须安全玻璃并核对净开口。按当地规范与防水系统确定墙面防水范围。',
'洗衣区设专用排水接口、防水地面和可检查阀；吊顶设检修口，禁止将漏水风险设备封死。'],width=458)
panel(48,260,'湿区及露台构造顺序',[
'湿区意向：结构基层 → 找平/找坡层 → 经确认的防水体系 → 保护/粘结层 → 防滑饰面。管根和阴阳角做系统配套加强；防水完成后检验合格再覆盖。',
'露台意向：主体结构 → 保温/找坡/防水组合系统 → 排水与保护层 → 户外防滑饰面。门槛、泛水、保温位置、排水口标高由专业统一设计。',
'栏杆固定和花池需独立结构、防水节点；种植不遮堵排水；不放置未经荷载复核的大型水缸、砌筑花池或重型设备。'],width=1090)
end()

new('V-01','装修后外观 · 三种风格','同一基础平面下的概念建模；B、C作为造型参考，需另行深化屋面和附属构造')
for i,name in enumerate(['01_现代简约','02_新中式','03_乡村坡屋顶']):
    pdf.drawImage(str(IMG/(name+'.png')),35+i*385,300,width=375,height=281)
    text(80+i*385,265,['A 现代简约 / 主方案','B 新中式 / 饰面与线条','C 坡屋顶 / 限高待核'][i],12,TEAL)
para(70,190,'图像由本地三维几何建模绘制，外墙范围、楼层高度、主要开口和西南露台依据本册方案；材质、阴影、绿化和室外台阶为视觉表达。它们不是AI写实照片，也未模拟真实日照或周边环境。',1050,12,22)
end()

new('V-02','装修示意 · 客餐厅与老人房','轴测剖开视角；为观察室内，部分墙面、门窗与顶棚被隐藏')
pdf.drawImage(str(IMG/'living.png'),40,300,width=550,height=413)
pdf.drawImage(str(IMG/'bedroom.png'),600,300,width=550,height=413)
panel(60,245,'客餐厅', ['浅木地面、暖白墙面、灰米色沙发；餐厅在北、客厅在南，按首层西侧连续空间表达。'],width=500)
panel(640,245,'老人房', ['1500mm床、600mm深衣柜、低眩光与床边照明；材质和色彩可复用于二、三层卧室。'],width=490)
end()

new('X-01','下一步深化与交付说明','先确认空间和家庭使用方式，再交当地有资质的团队做施工设计')
panel(48,700,'业主需补充',[
'01 所在省市县、乡镇审批与限高、宅基地红线、四侧道路和邻宅、场地实测高差。',
'02 常住人数、老人行动能力、是否需要车库/电梯/神龛/农具储物/独立出租，以及是否保留三层露台。',
'03 主体和装修预算分别多少；外观A/B/C选择；供水来源、水压，供电相制和容量，天然气或液化气。',
'04 周边下水接驳、化粪池条件、雨水出口、当地冻土/台风/积雪/高地下水等条件。'],width=495)
panel(622,700,'专业设计与验收',[
'建筑：实测总图、退界、门窗表、净高、疏散、防火、日照采光、节能、无障碍及地方审批。',
'结构：地勘、基础、承重体系、抗震、梁柱板/楼梯配筋、开洞、露台与屋面设备荷载。',
'给排水：用水压力、管径、坡度、穿板及存水弯、通气、排水系统和防水节点；试压、通水、闭水验收。',
'电气：负荷计算、进线容量、线径与保护协调、接地防雷、等电位；绝缘、接地、漏保测试。',
'网络：弱电点位表、管道填充与弯曲半径、机柜通风、光纤预留、全链路测试和端口标识。',
'燃气：气源确认后交燃气单位完成设计安装及气密性验收，业主不据此图自行接管。'],width=495)
panel(48,330,'本次可交付文件',[
'完整PDF图册：平面3张、屋面、立面、楼梯控制、给排水3张及系统、强电3张及系统、网络3张、燃气、装修与效果。',
'images文件夹：三种外观和三张室内轴测PNG。pages文件夹：逐页高清图纸PNG。index.html：便于浏览图纸与下载图册。',
'build_design.py：可重复生成的绘图源文件。图纸采用统一尺寸参数；本次未提供DWG、结构施工图或真实工程算量文件。'],width=1090)
end()
pdf.save()
(ROOT/'page_index.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Generated {len(pages)} pages and 6 model illustrations in {ROOT}')
