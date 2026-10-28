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


FONT="C:/Windows/Fonts/simhei.ttf"
pdfmetrics.registerFont(TTFont("CN",FONT))
W,H=landscape(A3)
INK="#253943";TEAL="#186d71";MUTED="#62757c";PALE="#edf3f2";GOLD="#b68b52"
S=1000*mm/60;OX=100;OY=687

def font(size):
    return ImageFont.truetype(FONT, size)

def rgb(c):
    return tuple((int(c[i:i + 2], 16) for i in (1, 3, 5)))

def shade(c, k):
    return tuple((min(255, int(v * k)) for v in rgb(c)))

class Model:

    def __init__(self):
        self.faces = []

    def face(self, pts, col):
        self.faces.append((pts, col))

    def box(self, x, y, z, dx, dy, dz, col):
        self.face([(x, y + dy, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)], shade(col, 0.88))
        self.face([(x + dx, y, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x + dx, y, z + dz)], shade(col, 0.72))
        self.face([(x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)], shade(col, 1.08))

    def southwindow(self, x, y, z, w, h):
        self.box(x, y, z, w, 0.075, h, '#283e49')
        self.box(x + 0.08, y + 0.08, z + 0.08, w - 0.16, 0.018, h - 0.16, '#789ca7')
        self.box(x + w / 2 - 0.025, y + 0.105, z + 0.08, 0.05, 0.025, h - 0.16, '#d0d7d4')

    def eastwindow(self, x, y, z, w, h):
        self.box(x, y, z, 0.075, w, h, '#283e49')
        self.box(x + 0.08, y + 0.08, z + 0.08, 0.018, w - 0.16, h - 0.16, '#789ca7')
        self.box(x + 0.105, y + w / 2 - 0.025, z + 0.08, 0.025, 0.05, h - 0.16, '#d0d7d4')

    def render(self, path, title, subtitle, size=(2000, 1500), scale=82, center=(1000, 1130)):
        im = Image.new('RGB', size, '#eef0e9')
        raw = np.array([[0.8 * p[0] - 0.6 * p[1], 0.33 * p[0] + 0.44 * p[1] - 0.835 * p[2]] for f in self.faces for p in f[0]])
        lo = raw.min(axis=0)
        hi = raw.max(axis=0)
        scale = min((size[0] - 170) / (hi[0] - lo[0]), (size[1] - 350) / (hi[1] - lo[1]))
        center = ((size[0] - (hi[0] + lo[0]) * scale) / 2, 185 - lo[1] * scale)

        def proj(p):
            x, y, z = p
            return (center[0] + scale * (0.8 * x - 0.6 * y), center[1] + scale * (0.33 * x + 0.44 * y - 0.835 * z))
        pixels = np.array(im)
        depth = np.full((size[1], size[0]), -100000000.0, dtype=np.float32)
        for pts, col in self.faces:
            pp = np.array([proj(p) for p in pts])
            zz = np.array([0.501 * p[0] + 0.668 * p[1] + 0.55 * p[2] for p in pts])
            for ids in [(0, 1, 2), (0, 2, 3)] if len(pts) == 4 else [(0, 1, 2)]:
                tri = pp[list(ids)]
                z = zz[list(ids)]
                xmin = max(0, int(math.floor(tri[:, 0].min())))
                xmax = min(size[0] - 1, int(math.ceil(tri[:, 0].max())))
                ymin = max(0, int(math.floor(tri[:, 1].min())))
                ymax = min(size[1] - 1, int(math.ceil(tri[:, 1].max())))
                if xmin > xmax or ymin > ymax:
                    continue
                a, b, c = tri
                den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(den) < 1e-06:
                    continue
                yy, xx = np.mgrid[ymin:ymax + 1, xmin:xmax + 1]
                u = ((b[1] - c[1]) * (xx - c[0]) + (c[0] - b[0]) * (yy - c[1])) / den
                v = ((c[1] - a[1]) * (xx - c[0]) + (a[0] - c[0]) * (yy - c[1])) / den
                w = 1 - u - v
                dd = u * z[0] + v * z[1] + w * z[2]
                target = depth[ymin:ymax + 1, xmin:xmax + 1]
                mask = (u >= -1e-05) & (v >= -1e-05) & (w >= -1e-05) & (dd >= target - 1e-05)
                target[mask] = dd[mask]
                pixels[ymin:ymax + 1, xmin:xmax + 1][mask] = col
        im = Image.fromarray(pixels)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, size[0], 150), fill='#f8f8f2')
        d.text((75, 37), title, font=font(43), fill=INK)
        d.text((78, 99), subtitle, font=font(22), fill=MUTED)
        d.rectangle((0, size[1] - 78, size[0], size[1]), fill='#f8f8f2')
        d.text((75, size[1] - 54), '尺寸约束三维示意 · 材质与采光为表达效果 · 非实景照片', font=font(23), fill=MUTED)
        im.save(path)

def text(x, y, t, size=10, color=INK):
    t = t.replace('²', '2')
    pdf.setFont('CN', size)
    pdf.setFillColor(HexColor(color))
    pdf.drawString(x, y, t)

def line(x1, y1, x2, y2, color=INK, width=1, dash=None):
    pdf.setStrokeColor(HexColor(color))
    pdf.setLineWidth(width)
    pdf.setDash(dash or [])
    pdf.line(x1, y1, x2, y2)
    pdf.setDash([])

def rect(x, y, w, h, fill=None, stroke=INK, width=1):
    pdf.setLineWidth(width)
    pdf.setStrokeColor(HexColor(stroke))
    pdf.setFillColor(HexColor(fill or '#ffffff'))
    pdf.rect(x, y, w, h, fill=bool(fill), stroke=bool(stroke))

def wrap(t, width, size=10):
    t = t.replace('²', '2')
    out = []
    s = ''
    for ch in t:
        if pdfmetrics.stringWidth(s + ch, 'CN', size) > width and ch not in '。，；：、）】%':
            out.append(s)
            s = ch
        else:
            s += ch
    if s:
        out.append(s)
    return out

def para(x, y, t, width=490, size=11, leading=19, color=INK):
    for row in wrap(t, width, size):
        text(x, y, row, size, color)
        y -= leading
    return y

def panel(x, y, title, items, width=475):
    text(x, y, title, 14, TEAL)
    line(x, y - 10, x + width, y - 10, '#bfd0cc', 0.7)
    y -= 32
    for t in items:
        y = para(x, y, t, width, 10.7, 18) - 12
    return y

def p(x, y):
    return (OX + x * S, OY - y * S)

def wl(a, b, c=INK, w=1, dash=None):
    line(*p(*a), *p(*b), c, w, dash)

def wr(x, y, w, h, fill=None, stroke=INK, lw=0.6):
    xx, yy = p(x, y + h)
    rect(xx, yy, w * S, h * S, fill, stroke, lw)

def label(x, y, t, size=10, color=INK, center=True):
    xx, yy = p(x, y)
    pdf.setFont('CN', size)
    pdf.setFillColor(HexColor(color))
    (pdf.drawCentredString if center else pdf.drawString)(xx, yy, t)

def wall(a, b, width=0.12):
    wl(a, b, INK, width * S)

def door(x, y, w=0.9, orient='h', swing=1):
    if orient == 'h':
        wl((x, y), (x + w, y), '#ffffff', 0.15 * S)
        wl((x, y), (x, y + swing * w), MUTED, 0.7)
        xx, yy = p(x, y)
        pdf.setStrokeColor(HexColor('#a7b2b0'))
        pdf.setLineWidth(0.5)
        if swing == 1:
            pdf.arc(xx - w * S, yy - w * S, xx + w * S, yy + w * S, 270, 90)
        else:
            pdf.arc(xx - w * S, yy - w * S, xx + w * S, yy + w * S, 0, 90)
    else:
        wl((x, y), (x, y + w), '#ffffff', 0.15 * S)
        wl((x, y), (x + swing * w, y), MUTED, 0.7)
        xx, yy = p(x, y)
        pdf.setStrokeColor(HexColor('#a7b2b0'))
        pdf.setLineWidth(0.5)
        if swing == 1:
            pdf.arc(xx - w * S, yy - w * S, xx + w * S, yy + w * S, 270, 90)
        else:
            pdf.arc(xx - w * S, yy - w * S, xx + w * S, yy + w * S, 180, 90)

def window(x, y, w, orient='h'):
    if orient == 'h':
        wl((x, y), (x + w, y), '#ffffff', 0.245 * S)
        for d in [-0.07, 0, 0.07]:
            wl((x, y + d), (x + w, y + d), '#5795a1', 0.7)
    else:
        wl((x, y), (x, y + w), '#ffffff', 0.245 * S)
        for d in [-0.07, 0, 0.07]:
            wl((x + d, y), (x + d, y + w), '#5795a1', 0.7)

def sliding(x, y, w):
    wl((x, y), (x + w, y), '#ffffff', 0.15 * S)
    wl((x, y - 0.025), (x + w * 0.58, y - 0.025), MUTED, 0.8)
    wl((x + w * 0.42, y + 0.025), (x + w, y + 0.025), MUTED, 0.8)

def sliding_v(x, y, w):
    wl((x, y), (x, y + w), '#ffffff', 0.15 * S)
    wl((x - 0.025, y), (x - 0.025, y + w * 0.58), MUTED, 0.8)
    wl((x + 0.025, y + w * 0.42), (x + 0.025, y + w), MUTED, 0.8)

def dim(a, b, txt, offset=0.45):
    x1, y1 = a
    x2, y2 = b
    if abs(y1 - y2) < 0.001:
        y = y1 + offset
        wl((x1, y), (x2, y), MUTED, 0.5)
        for x in [x1, x2]:
            wl((x, y - 0.1), (x, y + 0.1), MUTED, 0.7)
            wl((x, y1), (x, y), MUTED, 0.3)
        label((x1 + x2) / 2, y - 0.1, txt, 8, MUTED)
    else:
        x = x1 + offset
        wl((x, y1), (x, y2), MUTED, 0.5)
        for y in [y1, y2]:
            wl((x - 0.1, y), (x + 0.1, y), MUTED, 0.7)
            wl((x1, y), (x, y), MUTED, 0.3)
        xx, yy = p(x - 0.12, (y1 + y2) / 2)
        pdf.saveState()
        pdf.translate(xx, yy)
        pdf.rotate(90)
        text(0, 0, txt, 8, MUTED)
        pdf.restoreState()

def symbol(x, y, t, color):
    xx, yy = p(x, y)
    pdf.setFillColor(white)
    pdf.setStrokeColor(HexColor(color))
    pdf.setLineWidth(1)
    pdf.circle(xx, yy, 8, fill=1, stroke=1)
    pdf.setFont('CN', 7)
    pdf.setFillColor(HexColor(color))
    pdf.drawCentredString(xx, yy - 2.4, t)

def route(pts, color, width=1.5, dash=None):
    for a, b in zip(pts, pts[1:]):
        wl(a, b, color, width, dash)

def bed(x, y, w=1.5, h=2):
    wr(x, y, w, h, '#e7e0d3', '#ae9c83')
    wr(x + 0.06, y + 0.09, w - 0.12, 0.35, '#faf8f1', '#ae9c83')
    wl((x, y + 0.55), (x + w, y + 0.55), '#ae9c83', 0.6)