"""Sinh hình minh họa các bộ phận hệ thống nhiệt (SVG, cùng một phong cách).
Chạy:  python tao_hinh.py      → tạo các file .svg trong thư mục này.
Hình là MINH HỌA kỹ thuật chung, không theo bản vẽ của VinFast."""
import math, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 960, 640
C = dict(hot='#E2552F', liq='#F0912A', cold='#2F86E0', batt='#14A892', motor='#D49A12', air='#9A78E0',
         hv='#F07A1A', sig='#C2418A', ink='#15212C', muted='#5A6775', line='#D0D8DF', bg='#F6F8FA', card='#FFFFFF',
         m1='#D5DCE2', m2='#AEB8C2', m3='#7E8A96', dark='#2E363F', dark2='#444E59')
FONT = "Segoe UI, Arial, sans-serif"

def esc(t): return html.escape(str(t))

def shade(hex_, k):
    h = hex_.lstrip('#'); r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    f = (lambda v: int(max(0, min(255, v*k)))) if k < 1 else (lambda v: int(min(255, v+(255-v)*(k-1))))
    return '#%02x%02x%02x' % (f(r), f(g), f(b))

class D:
    """Bản vẽ: các hàm vẽ trả về chuỗi SVG, cộng dồn vào self.s."""
    def __init__(self, ox=330, oy=330, S=1.0):
        self.s = []; self.ox, self.oy, self.S = ox, oy, S
    def add(self, x): self.s.append(x); return self
    # isometric
    def iso(self, x, y, z):
        c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
        return (self.ox + (x - y)*c*self.S, self.oy + (x + y)*s*self.S - z*self.S)
    def poly(self, pts, fill, stroke=None, sw=1, op=1):
        p = ' '.join('%.1f,%.1f' % q for q in pts)
        return self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke or shade(fill,0.7)}" stroke-width="{sw}" opacity="{op}" stroke-linejoin="round"/>')
    def box(self, x, y, z, w, d, h, col, op=1):
        I = self.iso
        self.poly([I(x+w,y,z), I(x+w,y+d,z), I(x+w,y+d,z+h), I(x+w,y,z+h)], shade(col,0.72), op=op)
        self.poly([I(x,y+d,z), I(x+w,y+d,z), I(x+w,y+d,z+h), I(x,y+d,z+h)], shade(col,0.86), op=op)
        self.poly([I(x,y,z+h), I(x+w,y,z+h), I(x+w,y+d,z+h), I(x,y+d,z+h)], shade(col,1.12), op=op)
        return self
    def fins_x(self, x, y, z, d, h, n, col='#00000033'):   # vertical lines on the +x face
        for i in range(1, n):
            t = y + d*i/n; a, b = self.iso(x, t, z), self.iso(x, t, z+h)
            self.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col}" stroke-width="1"/>')
        return self
    def fins_y(self, x, y, z, w, h, n, col='#00000033'):   # vertical lines on the +y face
        for i in range(1, n):
            t = x + w*i/n; a, b = self.iso(t, y, z), self.iso(t, y, z+h)
            self.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col}" stroke-width="1"/>')
        return self
    # 2D helpers
    def rect(self, x, y, w, h, fill, rx=4, stroke=None, sw=1.2, op=1, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        return self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke or shade(fill,0.7)}" stroke-width="{sw}" opacity="{op}"{da}/>')
    def circ(self, x, y, r, fill, stroke=None, sw=1.2, op=1):
        return self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke or shade(fill,0.7) if fill!="none" else C["ink"]}" stroke-width="{sw}" opacity="{op}"/>')
    def ell(self, x, y, rx, ry, fill, stroke=None, sw=1.2):
        return self.add(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke or shade(fill,0.7)}" stroke-width="{sw}"/>')
    def path(self, d, fill='none', stroke=None, sw=2, op=1, dash=None, cap='round'):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        return self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke or C["ink"]}" stroke-width="{sw}" opacity="{op}" stroke-linecap="{cap}" stroke-linejoin="round"{da}/>')
    def line(self, a, b, col, sw=2, dash=None, arrow=False):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        mk = f' marker-end="url(#ar_{col.lstrip("#")})"' if arrow else ''
        return self.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"{da}{mk}/>')
    def cyl_h(self, x, y, L, r, col, cap=True):          # horizontal cylinder, left end at x, centre line y
        self.rect(x, y-r, L, 2*r, shade(col,0.9), rx=0)
        self.add(f'<rect x="{x}" y="{y-r}" width="{L}" height="{r*0.55:.1f}" fill="{shade(col,1.25)}" opacity=".55"/>')
        if cap: self.ell(x+L, y, r*0.32, r, shade(col,1.1))
        return self
    def cyl_v(self, x, y, r, h, col):                     # vertical cylinder, top centre at (x,y)
        self.rect(x-r, y, 2*r, h, shade(col,0.88), rx=0)
        self.add(f'<rect x="{x-r}" y="{y}" width="{r*0.6:.1f}" height="{h}" fill="{shade(col,1.25)}" opacity=".45"/>')
        self.ell(x, y+h, r, r*0.32, shade(col,0.8)); self.ell(x, y, r, r*0.32, shade(col,1.12))
        return self
    def port(self, a, b, col, w=9):                       # coloured pipe stub a→b
        return self.line(a, b, col, sw=w).line(a, b, shade(col,1.35), sw=w*0.35)
    def flow(self, a, b, col, sw=2.5):                    # flow arrow
        return self.line(a, b, col, sw=sw, arrow=True)
    def call(self, p, q, text, anchor='start'):           # callout from part p to label at q
        self.add(f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{C["ink"]}" stroke-width="1" opacity=".55"/>')
        self.add(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3.2" fill="{C["ink"]}"/>')
        dx = 5 if anchor=='start' else -5
        lines = text.split('\n')
        for i, t in enumerate(lines):
            self.add(f'<text x="{q[0]+dx:.1f}" y="{q[1]+4+i*15:.1f}" font-size="13" font-weight="{600 if i==0 else 400}" fill="{C["ink"] if i==0 else C["muted"]}" text-anchor="{anchor}">{esc(t)}</text>')
        return self
    def text(self, x, y, t, size=12, col=None, weight=400, anchor='middle'):
        return self.add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{col or C["muted"]}" font-weight="{weight}" text-anchor="{anchor}">{esc(t)}</text>')

def wrap(t, n):
    out, cur = [], ''
    for w in t.split():
        if len(cur) + len(w) + 1 > n: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: out.append(cur)
    return out

LEG = {'hot':'Gas nóng cao áp', 'liq':'Gas lỏng cao áp', 'cold':'Gas lạnh thấp áp', 'batt':'Nước làm mát pin',
       'motor':'Nước làm mát motor', 'air':'Luồng gió', 'hv':'Điện cao áp', 'sig':'Tín hiệu / CAN'}

def page(num, slug, title, en, where, loop, d, info, legend):
    defs = ''.join(f'<marker id="ar_{v.lstrip("#")}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{v}"/></marker>' for v in list(C.values()) + ['#7FB3E6'] if v.startswith('#'))
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<defs>{defs}</defs>', f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>',
         f'<text x="32" y="46" font-size="26" font-weight="700" fill="{C["ink"]}">{esc(title)}</text>',
         f'<text x="32" y="70" font-size="14" fill="{C["muted"]}">{esc(en)} · {esc(where)} · {esc(loop)}</text>',
         f'<line x1="32" y1="84" x2="{W-32}" y2="84" stroke="{C["line"]}"/>',
         f'<text x="{W-32}" y="46" font-size="13" fill="{C["muted"]}" text-anchor="end">#{num:02d}</text>']
    s.append('<g transform="translate(14,34) scale(0.86)">'); s += d.s; s.append('</g>')
    # info card
    x0, y0, cw = 652, 104, 276
    s.append(f'<rect x="{x0}" y="{y0}" width="{cw}" height="{H-y0-58}" rx="10" fill="{C["card"]}" stroke="{C["line"]}"/>')
    y = y0 + 28
    for head, body in info:
        s.append(f'<text x="{x0+16}" y="{y}" font-size="11" font-weight="700" letter-spacing="1.2" fill="{C["muted"]}">{esc(head.upper())}</text>'); y += 18
        items = body if isinstance(body, list) else [body]
        for it in items:
            bullet = isinstance(body, list)
            for j, ln in enumerate(wrap(it, 36 if bullet else 38)):
                s.append(f'<text x="{x0+16+(12 if bullet else 0)}" y="{y}" font-size="12.5" fill="{C["ink"]}">{esc(ln)}</text>')
                if bullet and j == 0: s.append(f'<circle cx="{x0+20}" cy="{y-4}" r="2.2" fill="{C["hot"]}"/>')
                y += 16
            y += 2
        y += 12
    # legend
    lx = 32
    for k in legend:
        s.append(f'<rect x="{lx}" y="{H-44}" width="18" height="6" rx="3" fill="{C[k]}"/><text x="{lx+24}" y="{H-37}" font-size="12" fill="{C["muted"]}">{esc(LEG[k])}</text>')
        lx += 30 + len(LEG[k])*6.6
    s.append(f'<text x="{W-32}" y="{H-20}" font-size="11" fill="{C["muted"]}" text-anchor="end">Hình minh họa kỹ thuật chung — không theo bản vẽ VinFast</text>')
    s.append('</svg>')
    fn = os.path.join(HERE, f'{num:02d}_{slug}.svg')
    open(fn, 'w', encoding='utf-8').write('\n'.join(s))
    return fn

PAGES = []
def reg(fn): PAGES.append(fn); return fn

# ---------------------------------------------------------------- 00 tổng thể
def p00():
    d = D()
    def blk(x, y, w, h, t, col, sub=''):
        d.rect(x, y, w, h, '#FFFFFF', rx=8, stroke=col, sw=2)
        d.text(x+w/2, y+h/2+(0 if sub else 5), t, 13, C['ink'], 600)
        if sub: d.text(x+w/2, y+h/2+18, sub, 11)
    # gas loop
    d.text(180, 117, 'VÒNG GAS LẠNH', 11, C['cold'], 700, 'start')
    blk(40, 124, 110, 50, 'Máy nén', C['hot'], 'điện, cao áp'); blk(210, 124, 110, 50, 'Dàn nóng', C['hot'], '+ quạt két')
    blk(380, 124, 90, 50, 'EXV', C['liq']); blk(510, 124, 110, 50, 'Dàn lạnh', C['cold'], 'trong HVAC')
    blk(380, 196, 90, 44, 'Van chiller', C['liq']); blk(510, 196, 110, 44, 'CHILLER', C['batt'], 'gas ↔ nước')
    d.flow((150,149),(206,149),C['hot']); d.flow((320,149),(376,149),C['liq']); d.flow((470,149),(506,149),C['cold'])
    d.path('M 345 174 L 345 218 L 376 218', stroke=C['liq'], sw=2.5); d.flow((470,218),(506,218),C['cold'])
    d.path('M 565 124 L 565 100 L 95 100 L 95 120', stroke=C['cold'], sw=2.5, dash='6 4')
    # battery loop
    d.text(40, 280, 'VÒNG NƯỚC PIN', 11, C['batt'], 700, 'start')
    blk(40, 292, 110, 46, 'Bơm pin', C['batt']); blk(210, 292, 110, 46, 'PTC nước', C['hot'])
    blk(380, 292, 150, 46, 'Tấm làm mát pin', C['batt'], 'dưới các module')
    blk(560, 292, 70, 46, 'Van', C['motor'], '4 ngả')
    d.flow((150,315),(206,315),C['batt']); d.flow((320,315),(376,315),C['batt']); d.flow((530,315),(556,315),C['batt'])
    d.path('M 565 240 L 565 262 L 95 262 L 95 288', stroke=C['batt'], sw=2.5)
    d.path('M 595 338 L 595 352 L 95 352 L 95 340', stroke=C['batt'], sw=2.5, dash='6 4')
    # motor loop
    d.text(40, 392, 'VÒNG NƯỚC MOTOR', 11, C['motor'], 700, 'start')
    blk(40, 404, 100, 46, 'Bơm motor', C['motor']); blk(170, 404, 110, 46, 'OBC · DC-DC', C['motor'])
    blk(310, 404, 120, 46, 'Inverter · Motor', C['motor']); blk(460, 404, 100, 46, 'Két nước', C['motor'], '+ quạt két')
    d.flow((140,427),(166,427),C['motor']); d.flow((280,427),(306,427),C['motor']); d.flow((430,427),(456,427),C['motor'])
    d.path('M 510 450 L 510 470 L 90 470 L 90 452', stroke=C['motor'], sw=2.5)
    d.path('M 595 338 L 595 427 L 564 427', stroke=C['motor'], sw=2, dash='3 4')
    d.text(612, 400, 'nối khi cần', 10, C['motor'], 400, 'start')
    # HVAC
    d.text(40, 506, 'HỘP HVAC CABIN', 11, C['air'], 700, 'start')
    for i, t in enumerate(['Lọc gió', 'Blower', 'Dàn lạnh', 'PTC / dàn ngưng', 'Cửa gió → cabin']):
        blk(40+i*120, 518, 108, 40, t, C['air'])
        if i: d.flow((40+i*120-12, 538), (40+i*120-2, 538), C['air'])
    info = [('Ba vòng + một hộp', 'Vòng gas lạnh làm lạnh cabin (qua dàn lạnh) và pin (qua chiller). Vòng nước pin giữ pin 20–40°C. Vòng nước motor thải nhiệt motor, inverter, OBC, DC-DC ra két nước. Hộp HVAC đưa gió đã làm lạnh / sưởi vào cabin.'),
            ('Hai cầu nối', ['Chiller: gas lạnh làm lạnh nước của pin', 'Van chia nước: nối vòng motor sang vòng pin để tận dụng nhiệt']),
            ('Điều khiển', 'VCU, BMS, CCU đọc cảm biến và bật / tắt máy nén, van, bơm, quạt, PTC.')]
    return reg(page(0, 'so_do_tong_the', 'Sơ đồ tổng thể hệ thống nhiệt', 'Thermal system overview', 'toàn xe', 'sơ đồ khối', d, info, ['hot','liq','cold','batt','motor','air']))

# ---------------------------------------------------------------- linh kiện
def p01():
    d = D(ox=300, oy=380, S=1.0)
    d.rect(150, 300, 30, 70, C['m3'], rx=3); d.rect(440, 300, 30, 70, C['m3'], rx=3)       # chân đế
    d.cyl_h(120, 290, 380, 82, C['m1'])                                                    # thân máy nén
    for i in range(6): d.line((180+i*40, 210), (180+i*40, 370), '#00000022', sw=1)
    d.box(-30, -30, 172, 150, 80, 34, C['dark2'])                                           # biến tần tích hợp
    d.port((516, 240), (600, 240), C['cold']); d.port((516, 340), (600, 340), C['hot'])
    d.ell(504, 290, 20, 60, shade(C['m2'], 1.0))
    d.rect(262, 112, 46, 24, C['hv'], rx=4)                                                 # đầu nối cao áp
    d.call((300, 160), (180, 128), 'Biến tần tích hợp\nđiều khiển tốc độ', 'end')
    d.call((285, 116), (330, 100), 'Đầu nối cao áp', 'start')
    d.call((300, 300), (250, 440), 'Cụm nén xoắn ốc (scroll)\ntrong vỏ nhôm')
    d.call((590, 240), (620, 205), 'Cổng hút\ngas lạnh', 'start')
    d.call((590, 340), (620, 375), 'Cổng đẩy\ngas nóng', 'start')
    info = [('Chức năng', 'Hút gas thấp áp từ dàn lạnh / chiller, nén lên áp cao và nóng. Chạy bằng điện cao áp qua biến tần, tốc độ thay đổi theo nhu cầu làm lạnh.'),
            ('Hay hỏng', ['Kẹt cơ khí, mòn', 'Hỏng mạch biến tần', 'Mất cách điện (dầu bẩn)', 'Thiếu dầu do rò gas']),
            ('Telemetry', ['EAC Compressor Fault Status (cờ)', 'Không có tốc độ / công suất máy nén'])]
    return reg(page(1, 'may_nen_dien', 'Máy nén điện (EAC)', 'Electric A/C compressor', 'khoang trước', 'vòng gas lạnh', d, info, ['hot','cold','hv']))

def panel_hx(d, x, y, w, h, fin, tank):
    """Bộ trao đổi nhiệt dạng tấm lá (dàn nóng, két nước, dàn lạnh) — nhìn chính diện 3/4."""
    d.add(f'<polygon points="{x},{y} {x+w},{y-30} {x+w},{y+h-30} {x},{y+h}" fill="{fin}" stroke="{shade(fin,0.65)}" stroke-width="1.5"/>')
    for i in range(1, 46):
        t = i/46; xa = x + w*t
        d.line((xa, y - 30*t), (xa, y + h - 30*t), '#00000026', sw=1)
    for j in range(1, 8):
        t = j/8; d.line((x, y + h*t), (x+w, y - 30 + h*t), '#ffffff66', sw=1.4)
    d.add(f'<polygon points="{x-22},{y-6} {x},{y} {x},{y+h} {x-22},{y+h-6}" fill="{tank}" stroke="{shade(tank,0.65)}"/>')
    d.add(f'<polygon points="{x+w},{y-30} {x+w+22},{y-36} {x+w+22},{y+h-36} {x+w},{y+h-30}" fill="{tank}" stroke="{shade(tank,0.65)}"/>')

def p02():
    d = D(); panel_hx(d, 120, 170, 400, 260, '#E8C4B5', C['m2'])
    d.port((98, 200), (50, 200), C['hot']); d.port((564, 390), (612, 390), C['liq'])
    for k in range(4): d.flow((80+k*130, 470), (110+k*130, 445), '#7FB3E6', sw=2)
    d.text(300, 500, 'gió đầu xe / quạt két thổi qua', 12)
    d.call((320, 260), (330, 128), 'Lá tản nhiệt + ống dẹt nhôm')
    d.call((109, 330), (40, 520), 'Bình chứa hai bên', 'start')
    d.call((60, 200), (60, 160), 'Gas nóng vào', 'start')
    d.call((600, 390), (600, 430), 'Gas lỏng ra', 'start')
    info = [('Chức năng', 'Gas nóng cao áp đi qua các ống dẹt, nhả nhiệt ra gió đầu xe và ngưng tụ thành lỏng. Đặt trước két nước để nhận gió mát nhất.'),
            ('Hay hỏng', ['Bám bẩn, côn trùng', 'Lá móp, đá văng thủng → rò gas']),
            ('Telemetry', ['Không có áp suất cao áp', 'Thấy gián tiếp: điều hòa yếu khi xe đứng'])]
    return reg(page(2, 'dan_nong', 'Dàn nóng (condenser)', 'Condenser', 'đầu xe, sau cản', 'vòng gas lạnh', d, info, ['hot','liq','air']))

def fan2d(d, cx, cy, r, blades=7):
    d.circ(cx, cy, r+10, '#3A434D'); d.circ(cx, cy, r+2, '#1E252C')
    for k in range(blades):
        a = 2*math.pi*k/blades
        p1 = (cx + 18*math.cos(a), cy + 18*math.sin(a)); p2 = (cx + r*math.cos(a+0.35), cy + r*math.sin(a+0.35))
        p3 = (cx + r*math.cos(a+0.75), cy + r*math.sin(a+0.75)); p4 = (cx + 18*math.cos(a+0.6), cy + 18*math.sin(a+0.6))
        d.path(f'M {p1[0]:.1f} {p1[1]:.1f} Q {cx+0.7*r*math.cos(a+0.1):.1f} {cy+0.7*r*math.sin(a+0.1):.1f} {p2[0]:.1f} {p2[1]:.1f} L {p3[0]:.1f} {p3[1]:.1f} Q {cx+0.6*r*math.cos(a+0.75):.1f} {cy+0.6*r*math.sin(a+0.75):.1f} {p4[0]:.1f} {p4[1]:.1f} Z', fill='#6B7682', stroke='#2E363F', sw=1)
    d.circ(cx, cy, 22, C['dark2']); d.circ(cx, cy, 9, C['m2'])

def p03():
    d = D(); d.rect(70, 140, 520, 330, '#2E363F', rx=16)
    fan2d(d, 200, 305, 120); fan2d(d, 460, 305, 120)
    d.path('M 330 470 C 330 520 420 520 420 560', stroke=C['sig'], sw=2.5); d.rect(400, 556, 40, 18, C['dark'], rx=3)
    d.call((90, 160), (60, 118), 'Khung che (shroud)', 'start')
    d.call((300, 230), (330, 112), 'Cánh quạt')
    d.call((460, 305), (610, 250), 'Mô-tơ quạt\n(điều khiển PWM)', 'start')
    d.call((420, 565), (470, 590), 'Dây điều khiển từ VCU', 'start')
    info = [('Chức năng', 'Hút gió qua dàn nóng và két nước khi xe chạy chậm hoặc đứng yên (đang sạc). Dùng chung cho vòng gas và vòng nước motor.'),
            ('Hay hỏng', ['Mô-tơ cháy, kẹt ổ bi', 'Lỗi điều khiển PWM', 'Gãy cánh do vật lạ']),
            ('Telemetry', ['VCU Fan component error level (cờ)', 'Không có duty / tốc độ quạt']),
            ('Khi hỏng', 'Điều hòa yếu khi xe đứng, chiller yếu → sạc chậm, motor nóng → giảm công suất.')]
    return reg(page(3, 'quat_ket', 'Quạt két', 'Radiator / condenser fan', 'sau dàn nóng và két nước', 'dùng chung', d, info, ['sig']))

def p04():
    d = D(); panel_hx(d, 120, 175, 400, 250, '#E9D7A8', '#55606B')
    d.port((98, 205), (50, 205), C['motor']); d.port((564, 385), (612, 385), shade(C['motor'], 0.8))
    d.cyl_v(560, 120, 14, 18, C['dark2'])
    d.call((320, 260), (330, 128), 'Lõi tản nhiệt (ống + lá nhôm)')
    d.call((60, 205), (60, 165), 'Nước nóng từ motor vào', 'start')
    d.call((600, 385), (600, 425), 'Nước đã làm mát ra', 'start')
    d.call((109, 350), (40, 520), 'Bình góp nhựa', 'start')
    info = [('Chức năng', 'Thải nhiệt của nước vòng motor (motor, inverter, OBC, DC-DC) ra không khí nhờ gió đầu xe và quạt két.'),
            ('Hay hỏng', ['Tắc lõi (cặn, bụi bám ngoài)', 'Rò ở bình góp / mối nối']),
            ('Telemetry', ['Cờ “nước làm mát EDS quá nóng”', 'Không có nhiệt nước vào / ra két'])]
    return reg(page(4, 'ket_nuoc', 'Két nước (radiator)', 'Radiator', 'đầu xe, sau dàn nóng', 'vòng nước motor', d, info, ['motor','air']))

def p05():
    d = D(); d.rect(90, 170, 470, 260, '#3A434D', rx=10); d.rect(104, 184, 442, 232, '#1E252C', rx=6)
    for i in range(6):
        y = 205 + i*36; ang = -35 if i < 3 else 0
        d.add(f'<rect x="114" y="{y-6}" width="422" height="14" rx="4" fill="#7E8A96" stroke="#3A434D" transform="rotate({ang*0.25} 325 {y})"/>')
    d.box(-120, 210, 0, 60, 40, 50, C['dark2'])
    d.call((325, 210), (330, 130), 'Lá chắn (đang mở)')
    d.call((325, 350), (330, 470), 'Lá chắn (đang đóng)')
    d.call((150, 300), (40, 470), 'Mô-tơ chấp hành', 'start')
    d.flow((560, 230), (610, 230), '#7FB3E6'); d.text(605, 215, 'gió', 12)
    info = [('Chức năng', 'Đóng / mở lá chắn ở cản trước: đóng để giảm cản gió và giữ nhiệt khi trời lạnh, mở khi dàn nóng / két nước cần gió.'),
            ('Hay hỏng', ['Kẹt đóng → thiếu gió làm mát', 'Kẹt mở → tốn điện, sưởi chậm', 'Mô-tơ chấp hành hỏng']),
            ('Telemetry', ['VCU Ags component error level', 'Active Grille Shutters stuck (đèn báo)'])]
    return reg(page(5, 'luoi_tan_nhiet_ags', 'Lưới tản nhiệt chủ động (AGS)', 'Active grille shutter', 'cản trước', 'dùng chung', d, info, ['air']))

def p06():
    d = D(); d.box(-70, -40, 0, 140, 90, 70, C['m1'])
    d.cyl_v(300, 120, 52, 120, C['dark2']); d.rect(274, 150, 52, 30, C['sig'], rx=4)
    d.port((235, 335), (110, 335), C['liq']); d.port((420, 335), (500, 335), C['cold'])
    d.rect(290, 300, 20, 60, '#FFFFFF', rx=3, stroke=C['ink'], dash='3 3'); d.path('M 300 300 L 300 345 L 293 355 L 307 355 Z', fill=C['m3'], stroke=C['ink'], sw=1)
    d.call((300, 200), (420, 150), 'Mô-tơ bước\nđiều khiển độ mở', 'start')
    d.call((300, 168), (200, 128), 'Giắc tín hiệu', 'end')
    d.call((300, 350), (200, 420), 'Kim van (mặt cắt):\nbóp nghẹt dòng gas', 'end')
    d.call((120, 335), (90, 300), 'Gas lỏng\ncao áp vào', 'end')
    d.call((490, 335), (520, 300), 'Gas lạnh\nthấp áp ra', 'start')
    info = [('Chức năng', 'Bóp nghẹt dòng gas lỏng → áp suất và nhiệt độ tụt mạnh, tạo gas lạnh vào dàn lạnh hoặc chiller. Độ mở điều khiển điện tử.'),
            ('Hay hỏng', ['Kẹt (cặn, ẩm đóng băng)', 'Mở sai độ, mô-tơ bước hỏng']),
            ('Telemetry', ['Không có lệnh / vị trí EXV', 'Chỉ có VCU Valve error level'])]
    return reg(page(6, 'van_tiet_luu_exv', 'Van tiết lưu điện tử (EXV)', 'Electronic expansion valve', 'sát vách ngăn / trên chiller', 'vòng gas lạnh', d, info, ['liq','cold','sig']))

def p07():
    d = D(ox=300, oy=360); d.box(-80, -40, 0, 200, 110, 120, '#BFD6E6')
    d.fins_x(120, -40, 0, 110, 120, 22, '#2F86E033')
    for k in range(9):
        a, b = d.iso(-80 + k*25, 70, 0), d.iso(-80 + k*25, 70, 120)
        d.line(a, b, '#14A89255', sw=1.5)
    d.port((395, 205), (450, 175), C['cold']); d.port((425, 260), (480, 230), C['cold'])
    d.port((230, 405), (175, 440), C['batt']); d.port((310, 425), (255, 460), C['batt'])
    d.cyl_v(330, 120, 18, 40, C['dark2'])
    d.call((330, 140), (430, 118), 'Van chiller (EXV)', 'start')
    d.call((300, 300), (30, 520), 'Các tấm xếp chồng: gas và nước chảy xen kẽ', 'start')
    d.call((455, 175), (490, 150), 'Gas lạnh vào / ra', 'start')
    d.call((175, 440), (40, 470), 'Nước pin vào / ra', 'start')
    info = [('Chức năng', 'Bộ trao đổi nhiệt dạng tấm: gas lạnh hút nhiệt của nước vòng pin → nước xuống khoảng 15–20°C rồi về pin. Cầu nối giữa điều hòa và pin.'),
            ('Hay hỏng', ['Đóng cặn phía nước', 'Rò (gas hoặc nước)', 'Van chiller kẹt']),
            ('Telemetry', ['BMS yêu cầu làm mát (kW)', 'Nhiệt nước vào / ra pin', 'Không có trạng thái chiller'])]
    return reg(page(7, 'chiller', 'Chiller', 'Battery chiller (plate heat exchanger)', 'khoang trước', 'gas ↔ nước pin', d, info, ['cold','batt']))

def p08():
    d = D(); panel_hx(d, 150, 190, 330, 220, '#C8DCF0', C['m2'])
    d.port((128, 215), (80, 215), C['cold']); d.port((128, 380), (80, 380), C['cold'])
    for k in range(4): d.flow((560, 250+k*40), (500, 250+k*40-14), C['air'], sw=2)
    for k in range(4): d.flow((140, 260+k*35), (90, 260+k*35), '#7FB3E6', sw=2)
    for k in range(5): d.circ(200+k*55, 432, 4, '#7FB3E6', stroke='#2F86E0')
    d.call((310, 280), (320, 130), 'Lá + ống (gas bay hơi bên trong)')
    d.call((310, 432), (330, 480), 'Nước ngưng tụ → ống xả')
    d.call((560, 250), (600, 220), 'Gió ấm từ blower', 'start')
    d.call((90, 260), (60, 470), 'Gió lạnh ra cabin', 'start')
    info = [('Chức năng', 'Gas lạnh bay hơi bên trong, hút nhiệt của gió do blower thổi qua → gió lạnh vào cabin. Đồng thời ngưng hơi nước, làm khô gió.'),
            ('Hay hỏng', ['Đóng băng', 'Bẩn, mốc (mùi hôi)', 'Rò gas']),
            ('Telemetry', ['Actual evaporator temperature', 'Interior temperature'])]
    return reg(page(8, 'dan_lanh', 'Dàn lạnh (evaporator)', 'Evaporator', 'trong hộp HVAC sau taplo', 'gas lạnh ↔ gió', d, info, ['cold','air']))

def p09():
    d = D(); d.cyl_h(140, 300, 230, 62, C['dark2'], cap=False)
    d.circ(400, 300, 92, C['m1']); d.circ(400, 300, 64, '#FFFFFF', stroke=C['m3'], sw=1.5)
    for k in range(6):
        a = k*math.pi/3; d.path(f'M 400 300 Q {400+40*math.cos(a+0.5):.1f} {300+40*math.sin(a+0.5):.1f} {400+60*math.cos(a+0.9):.1f} {300+60*math.sin(a+0.9):.1f}', stroke=C['m3'], sw=4)
    d.port((400, 210), (400, 150), C['batt']); d.port((470, 245), (540, 210), C['batt'])
    d.rect(120, 270, 30, 60, C['sig'], rx=4)
    d.call((250, 290), (200, 400), 'Mô-tơ điện không chổi than', 'end')
    d.call((400, 300), (520, 360), 'Buồng xoắn + cánh bơm\n(mặt cắt)', 'start')
    d.call((400, 160), (430, 128), 'Nước vào (tâm)', 'start')
    d.call((530, 215), (560, 180), 'Nước ra (tiếp tuyến)', 'start')
    d.call((135, 300), (40, 200), 'Giắc điều khiển', 'start')
    info = [('Chức năng', 'Bơm điện đẩy nước làm mát đi vòng. Xe thường có 2 bơm: một cho vòng pin, một cho vòng motor.'),
            ('Hay hỏng', ['Mòn cánh, kẹt ổ bi', 'Lỗi điện / điều khiển', 'Có khí trong vòng → chạy không tải']),
            ('Telemetry', ['Battery / Motor electronic pump state', 'Water pump failure (cờ)', 'Không có tốc độ bơm'])]
    return reg(page(9, 'bom_nuoc', 'Bơm nước điện', 'Electric coolant pump', 'khoang trước, phía dưới', 'vòng pin / motor', d, info, ['batt','sig']))

def p10():
    d = D(ox=300, oy=380); d.box(-90, -50, 0, 180, 120, 90, '#5E3A33')
    for k in range(7):
        a, b = d.iso(-90 + 20 + k*22, -50, 90), d.iso(-90 + 20 + k*22, 70, 90)
        d.line(a, b, '#E2552F', sw=3)
    d.port((215, 340), (160, 370), C['batt']); d.port((470, 300), (530, 270), C['batt'])
    d.rect(330, 180, 50, 26, C['hv'], rx=4)
    d.call((330, 258), (330, 128), 'Điện trở PTC + lá nhôm trao đổi nhiệt')
    d.call((355, 190), (450, 160), 'Đầu nối cao áp', 'start')
    d.call((165, 370), (100, 410), 'Nước pin vào', 'end')
    d.call((525, 270), (560, 240), 'Nước ấm ra', 'start')
    info = [('Chức năng', 'Điện trở cao áp hâm nóng nước vòng pin khi trời lạnh, hoặc làm ấm pin trước khi sạc nhanh (preconditioning).'),
            ('Hay hỏng', ['Đứt điện trở', 'Rơ-le / mạch cao áp hỏng']),
            ('Telemetry', ['PTC module failure (cờ)', 'Battery pack precondition information', 'Không có công suất PTC']),
            ('Khi hỏng', 'Mùa đông pin lạnh → sạc nhanh rất chậm (bài A).')]
    return reg(page(10, 'ptc_nuoc', 'Sưởi PTC nước (vòng pin)', 'High-voltage coolant heater', 'khoang trước', 'vòng nước pin', d, info, ['batt','hv']))

def p11():
    d = D(); d.rect(120, 170, 400, 250, C['m2'], rx=6)
    for i in range(5):
        y = 190 + i*46; d.rect(132, y, 376, 18, '#C86B4F', rx=3)
        for k in range(12): d.rect(140 + k*30, y+4, 18, 10, '#F2E2C9', rx=2, stroke='#8B5A3C', sw=0.8)
    for k in range(4): d.flow((80, 220+k*50), (115, 220+k*50), '#7FB3E6', sw=2.5); d.flow((525, 220+k*50), (570, 220+k*50), C['hot'], sw=2.5)
    d.rect(250, 140, 60, 26, C['hv'], rx=4)
    d.call((200, 199), (200, 128), 'Viên gốm PTC', 'end')
    d.call((420, 245), (430, 470), 'Lá nhôm tản nhiệt')
    d.call((280, 150), (380, 118), 'Cực cao áp', 'start')
    d.call((90, 220), (60, 480), 'Gió lạnh vào', 'start'); d.call((560, 220), (600, 480), 'Gió ấm ra', 'start')
    info = [('Chức năng', 'Điện trở gốm PTC đặt trong luồng gió, sưởi cabin trên xe không có heat pump. Gốm PTC tự giới hạn nhiệt nên an toàn.'),
            ('Hay hỏng', ['Đứt viên gốm / cực', 'Rơ-le, mạch cao áp hỏng']),
            ('Telemetry', ['PTC module failure (cờ)', 'Interior temperature', 'Không có công suất PTC, nhiệt gió ra'])]
    return reg(page(11, 'ptc_gio', 'Sưởi PTC gió', 'PTC air heater', 'trong hộp HVAC', 'sưởi cabin', d, info, ['air','hot','hv']))

def p12():
    d = D(); d.rect(200, 160, 240, 300, '#EEF3F6', rx=18, stroke=C['m3'], sw=2)
    d.rect(204, 300, 232, 156, '#9FE0D3', rx=14, stroke='none')
    d.line((215, 230), (300, 230), C['hot'], sw=1.5, dash='5 3'); d.text(305, 234, 'MAX', 11, C['hot'], 700, 'start')
    d.line((215, 330), (300, 330), C['hot'], sw=1.5, dash='5 3'); d.text(305, 334, 'MIN', 11, C['hot'], 700, 'start')
    d.cyl_v(320, 128, 34, 30, C['dark2'])
    d.rect(412, 380, 28, 50, C['sig'], rx=4)
    d.port((260, 460), (260, 520), C['batt']); d.port((380, 460), (380, 520), C['batt'])
    d.call((320, 140), (420, 118), 'Nắp có van an toàn', 'start')
    d.call((300, 380), (120, 380), 'Nước làm mát\n50% glycol', 'end')
    d.call((426, 405), (470, 405), 'Cảm biến mức nước', 'start')
    d.call((300, 230), (120, 230), 'Vạch MIN–MAX', 'end')
    d.call((260, 510), (180, 540), 'Ống nối về vòng nước', 'end')
    info = [('Chức năng', 'Chứa phần nước dư khi giãn nở, tách bọt khí ra khỏi vòng nước, có cảm biến mức để cảnh báo thiếu nước.'),
            ('Hay hỏng', ['Nứt bình', 'Cảm biến mức kẹt']),
            ('Telemetry', ['Low level coolant water (cờ)', 'Không có giá trị mức nước']),
            ('Nguồn', 'VF 5: nước làm mát 50% glycol, có vạch MIN–MAX (đại lý VinFast).')]
    return reg(page(12, 'binh_nuoc_phu', 'Bình nước phụ + cảm biến mức', 'Expansion tank & level sensor', 'khoang trước, điểm cao nhất', 'vòng nước', d, info, ['batt','sig']))

def p13():
    d = D(); d.cyl_v(320, 220, 80, 150, C['m1'])
    d.box(-45, -45, 112, 90, 90, 40, C['dark2'])
    d.port((240, 290), (160, 290), C['batt']); d.port((400, 290), (480, 290), C['batt'])
    d.port((240, 340), (160, 340), C['motor']); d.port((400, 340), (480, 340), C['motor'])
    d.call((320, 140), (430, 118), 'Mô-tơ chấp hành', 'start')
    d.call((320, 320), (320, 470), 'Thân van xoay: đổi đường nối\ngiữa các cổng')
    d.call((170, 290), (110, 260), 'Cổng vòng pin', 'end'); d.call((170, 340), (110, 370), 'Cổng vòng motor', 'end')
    d.text(560, 270, 'Chế độ tách', 12, C['ink'], 600); d.text(560, 290, 'pin ⟲   motor ⟲', 12)
    d.text(560, 330, 'Chế độ nối', 12, C['ink'], 600); d.text(560, 350, 'motor → pin', 12)
    info = [('Chức năng', 'Chuyển hướng nước: tách vòng pin và vòng motor chạy riêng, hoặc nối tiếp để dùng nhiệt motor làm ấm pin (ITM trên VF 8 thế hệ mới).'),
            ('Hay hỏng', ['Kẹt ở một vị trí', 'Mô-tơ chấp hành hỏng, gãy bánh răng']),
            ('Telemetry', ['VCU Valve component error level', 'Không có vị trí van'])]
    return reg(page(13, 'van_chia_nuoc', 'Van chia nước nhiều ngả', 'Multi-way coolant valve', 'khoang trước', 'nối 2 vòng nước', d, info, ['batt','motor']))

def p14():
    d = D(ox=300, oy=330, S=0.78)
    d.box(-170, -70, 0, 330, 200, 16, '#8FD6C8')                                   # tấm làm mát
    for i in range(5):
        a, b = d.iso(-150, -50 + i*40, 16.5), d.iso(140, -50 + i*40, 16.5)
        d.line(a, b, C['batt'], sw=3)
        if i < 4:
            e = (-150, -50 + i*40) if i % 2 else (140, -50 + i*40)
            p, q = d.iso(e[0], e[1], 16.5), d.iso(e[0], e[1]+40, 16.5)
            d.line(p, q, C['batt'], sw=3)
    for i in range(4):
        for j in range(2):
            d.box(-160 + i*80, -60 + j*95, 70, 70, 85, 60, '#6E7E8C', op=0.95)
    d.box(170, -70, 0, 40, 60, 60, '#6B5B3E'); d.box(170, 30, 0, 40, 60, 40, C['dark2'])
    d.port(d.iso(-170, 120, 8), (d.iso(-170, 120, 8)[0]-60, d.iso(-170, 120, 8)[1]+30), C['batt'])
    d.port(d.iso(-170, 80, 8), (d.iso(-170, 80, 8)[0]-60, d.iso(-170, 80, 8)[1]+30), shade(C['batt'], 0.75))
    d.call(d.iso(0, 0, 130), (330, 112), 'Module cell (đặt trên tấm)', 'start')
    d.call(d.iso(60, 150, 16), (300, 540), 'Tấm làm mát: nước chảy trong kênh', 'start')
    d.call(d.iso(-160, 40, 18), (30, 200), 'Lớp keo tản nhiệt\ngiữa cell và tấm', 'start')
    d.call(d.iso(190, -40, 60), (520, 170), 'BDU\ncontactor, cầu chì', 'start')
    d.call(d.iso(190, 60, 40), (540, 420), 'BMS\nchính / phụ', 'start')
    d.call(d.iso(-170, 120, 8), (30, 470), 'Nước vào / ra pin\n(có cảm biến nhiệt)', 'start')
    info = [('Chức năng', 'Các module cell đặt trên tấm làm mát; nước chảy trong kênh của tấm để lấy nhiệt ra hoặc đưa nhiệt vào, giữ cell khoảng 20–45°C và đều nhau.'),
            ('Hay hỏng', ['Kênh tắc, rò nước trong pin', 'Keo tản nhiệt kém → cell nóng cục bộ']),
            ('Telemetry', ['Max / Min Cell Temperature', 'Nhiệt nước vào / ra pin', 'Coolant Leakage warning']),
            ('Nguồn', 'VF 5: pin LFP 116 cell, 7 khối, có cổng nước vào / ra (VATC).')]
    return reg(page(14, 'pin_tam_lam_mat', 'Pin cao áp + tấm làm mát', 'HV battery & cooling plate', 'dưới sàn xe', 'vòng nước pin', d, info, ['batt','hv']))

def p15():
    d = D(); d.cyl_h(130, 300, 330, 110, C['m2'])
    for k in range(9): d.path(f'M {160+k*34} 192 C {180+k*34} 250 {150+k*34} 350 {175+k*34} 408', stroke=C['motor'], sw=4, op=.85)
    d.circ(470, 300, 70, '#3A434D'); d.circ(470, 300, 46, '#B87333'); d.circ(470, 300, 22, C['m1'])
    d.line((470, 300), (600, 300), C['m3'], sw=14)
    d.port((200, 190), (200, 130), C['motor']); d.port((400, 410), (400, 470), shade(C['motor'], 0.8))
    d.call((280, 230), (300, 128), 'Áo nước quanh stator')
    d.call((470, 260), (540, 190), 'Stator (cuộn dây đồng)', 'start')
    d.call((470, 300), (560, 360), 'Rotor nam châm', 'start')
    d.call((590, 300), (610, 420), 'Trục ra hộp số', 'end')
    d.call((200, 140), (120, 118), 'Nước vào', 'end'); d.call((400, 465), (330, 510), 'Nước ra', 'end')
    info = [('Chức năng', 'Biến điện thành mô-men kéo bánh. Vỏ có áo nước để nước vòng motor mang nhiệt cuộn dây đi.'),
            ('Hay hỏng', ['Quá nhiệt cuộn dây → giảm công suất', 'Cảm biến nhiệt stator lỗi']),
            ('Telemetry', ['Motor Temperature', 'Cờ quá nhiệt motor (cảnh báo / lỗi)', 'Mô-men thực, tốc độ motor'])]
    return reg(page(15, 'motor_ao_nuoc', 'Motor kéo + áo nước', 'Traction motor & water jacket', 'trục trước / sau', 'vòng nước motor', d, info, ['motor']))

def p16():
    d = D(ox=320, oy=360); d.box(-120, -80, 0, 240, 180, 30, '#E9D7A8')
    for k in range(5):
        a, b = d.iso(-110 + k*50, -70, 31), d.iso(-110 + k*50, 90, 31)
        d.line(a, b, C['motor'], sw=3)
    for i in range(3): d.box(-100 + i*75, -50, 30, 60, 120, 22, C['dark2'])
    d.box(-120, -80, 52, 240, 180, 6, '#AEB8C2', op=0.35)
    d.rect(140, 300, 40, 26, C['hv'], rx=4); d.rect(470, 240, 70, 22, C['hv'], rx=4)
    d.port(d.iso(120, 100, 10), (d.iso(120, 100, 10)[0]+60, d.iso(120, 100, 10)[1]+30), C['motor'])
    d.call(d.iso(-70, 10, 52), (330, 118), 'Module IGBT / SiC (3 pha)')
    d.call(d.iso(0, 90, 30), (250, 500), 'Tấm làm mát có kênh nước', 'end')
    d.call((160, 312), (40, 250), 'Đầu vào DC từ pin', 'start'); d.call((505, 250), (560, 210), 'Ra 3 pha tới motor', 'start')
    info = [('Chức năng', 'Đổi DC từ pin thành AC 3 pha cho motor. Linh kiện công suất sinh nhiệt lớn khi tăng tốc mạnh nên đặt trên tấm làm mát bằng nước.'),
            ('Hay hỏng', ['Quá nhiệt IGBT → giảm công suất', 'Tấm làm mát tắc, thiếu nước']),
            ('Telemetry', ['EDS current temperature', 'Cờ quá nhiệt IGBT / drive plate', 'Power limitation warning'])]
    return reg(page(16, 'inverter_eds', 'Biến tần (inverter / EDS)', 'Traction inverter', 'gắn trên motor', 'vòng nước motor', d, info, ['motor','hv']))

def p17():
    d = D(ox=320, oy=380); d.box(-130, -90, 0, 260, 190, 90, '#56616C')
    d.fins_y(-130, 100, 90, 260, 0.1, 2)
    for k in range(10):
        a, b = d.iso(-120 + k*26, -90, 90), d.iso(-120 + k*26, 100, 90)
        d.line(a, b, '#3A434D', sw=2)
    d.rect(150, 300, 50, 30, C['hv'], rx=4); d.rect(470, 260, 40, 24, C['hv'], rx=4); d.rect(500, 300, 30, 20, '#2E363F', rx=3)
    d.port(d.iso(130, 80, 20), (d.iso(130, 80, 20)[0]+60, d.iso(130, 80, 20)[1]+30), C['motor'])
    d.call(d.iso(0, 0, 90), (330, 118), 'Vỏ chung "3-in-1": OBC + DC-DC + PDU')
    d.call((175, 315), (40, 255), 'Vào AC từ cổng sạc', 'start'); d.call((490, 272), (550, 230), 'Ra cao áp (pin)', 'start')
    d.call((515, 310), (560, 350), 'Ra 12V', 'start'); d.call(d.iso(130, 80, 20), (500, 470), 'Nước làm mát vào / ra', 'start')
    info = [('Chức năng', 'OBC đổi AC từ trụ sạc thường sang DC nạp pin; DC-DC hạ cao áp xuống 12V. Cả hai sinh nhiệt nên dùng chung nước vòng motor.'),
            ('Hay hỏng', ['Quá nhiệt khi sạc AC', 'DC-DC quá nhiệt → 12V yếu']),
            ('Telemetry', ['Charger Over Temperature Fault', 'DCDC Over Temperature Fault', 'DCDC Output Current']),
            ('Nguồn', 'VF 8 2023–2024: cụm 3-in-1; VF 8 thế hệ mới: tích hợp vào cụm động cơ 6-in-1.')]
    return reg(page(17, 'obc_dcdc', 'Bộ sạc OBC + DC-DC', 'On-board charger & DC-DC', 'khoang trước', 'vòng nước motor', d, info, ['motor','hv']))

def p18():
    d = D(); d.path('M 330 170 C 470 170 520 260 520 330 C 520 420 440 470 330 470 C 230 470 170 410 170 330 L 170 300 L 120 300 L 120 230 L 200 230 C 220 190 270 170 330 170 Z', fill='#3B3550', stroke='#26203A', sw=2)
    d.circ(340, 330, 98, '#5D5577'); d.circ(340, 330, 60, '#3B3550')
    for k in range(32):
        a = 2*math.pi*k/32; d.line((340 + 62*math.cos(a), 330 + 62*math.sin(a)), (340 + 96*math.cos(a+0.25), 330 + 96*math.sin(a+0.25)), C['air'], sw=3)
    d.circ(340, 330, 26, C['dark2'])
    d.flow((340, 120), (340, 165), C['air'], sw=3); d.flow((110, 265), (60, 265), C['air'], sw=3)
    d.call((340, 330), (560, 330), 'Mô-tơ blower', 'start')
    d.call((430, 280), (560, 220), 'Bánh lồng sóc', 'start')
    d.call((480, 420), (560, 450), 'Vỏ xoắn ốc', 'start')
    d.call((340, 130), (380, 112), 'Gió vào (qua lọc)', 'start'); d.call((70, 265), (60, 230), 'Gió ra dàn lạnh', 'start')
    info = [('Chức năng', 'Thổi gió (gió ngoài hoặc gió hồi) qua lọc → dàn lạnh → sưởi → cửa gió vào cabin. Mức gió do người lái hoặc chế độ auto chọn.'),
            ('Hay hỏng', ['Ổ bi mòn, kêu', 'Mô-tơ yếu, lỗi điều tốc']),
            ('Telemetry', ['Driver / Passenger Air Blow Level', 'Không có công suất / tốc độ blower'])]
    return reg(page(18, 'quat_gio_blower', 'Quạt gió cabin (blower)', 'HVAC blower', 'hộp HVAC, phía ghế phụ', 'gió cabin', d, info, ['air']))

def p19():
    d = D()
    def pleat(x, y, w, h, col, dirt=0):
        d.rect(x-8, y-8, w+16, h+16, '#E9E2CF' if not dirt else '#6B5B45', rx=4)
        pts = ' '.join(f'{x + i*w/24:.1f},{y + (0 if i % 2 == 0 else h):.1f}' for i in range(25))
        d.add(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
    pleat(80, 200, 220, 200, '#B8AE92'); pleat(360, 200, 220, 200, '#3E3226', dirt=1)
    for k in range(18): d.circ(380 + (k*53) % 200, 215 + (k*37) % 170, 3, '#2A221A')
    d.text(190, 440, 'Lọc sạch', 14, C['ink'], 600); d.text(470, 440, 'Lọc tắc (bụi, lá)', 14, C['ink'], 600)
    d.call((190, 300), (190, 128), 'Giấy lọc gấp nếp (+ than hoạt tính)')
    info = [('Chức năng', 'Lọc bụi, phấn hoa, PM2.5 trước khi gió vào hộp HVAC. VF 8 thế hệ mới dùng lọc Combi 1.0.'),
            ('Hay hỏng', ['Tắc do lâu không thay', 'Ẩm mốc → mùi hôi']),
            ('Telemetry', ['Không có tín hiệu trực tiếp', 'Thiếu công suất blower nên không phát hiện được']),
            ('Khi hỏng', 'Gió yếu dù blower chạy cùng mức, cabin lâu mát, tốn điện.')]
    return reg(page(19, 'loc_gio_cabin', 'Lọc gió cabin', 'Cabin air filter', 'trước blower', 'gió cabin', d, info, ['air']))

def p20():
    d = D(); d.rect(60, 150, 560, 340, '#EFEAF8', rx=14, stroke=C['air'], sw=2)
    d.rect(80, 250, 60, 140, '#E8E2CF', rx=4); d.text(110, 410, 'Lọc', 11)
    d.circ(190, 320, 40, '#5D5577'); d.text(190, 380, 'Blower', 11)
    d.rect(260, 220, 26, 200, '#C8DCF0', rx=3); d.text(273, 440, 'Dàn lạnh', 11)
    d.rect(400, 330, 22, 110, '#E58A62', rx=3); d.text(411, 460, 'PTC / sưởi', 11)
    d.path('M 330 320 L 395 280', stroke=C['dark'], sw=6); d.circ(330, 320, 6, C['dark'])
    d.path('M 520 200 L 560 180', stroke=C['dark'], sw=5); d.path('M 520 300 L 560 300', stroke=C['dark'], sw=5); d.path('M 520 400 L 560 420', stroke=C['dark'], sw=5)
    d.path('M 100 165 L 140 200', stroke=C['dark'], sw=5)
    for y, t in [(180, 'Sấy kính'), (300, 'Cửa gió mặt'), (420, 'Cửa gió chân')]:
        d.flow((565, y), (610, y), C['air'], sw=2.5); d.text(612, y+22, t, 11, C['ink'], 600, 'end')
    d.flow((300, 300), (380, 250), '#7FB3E6', sw=2.5); d.flow((300, 360), (395, 360), C['hot'], sw=2.5)
    d.call((362, 300), (300, 112), 'Cửa gió trộn: chia gió đi vòng hay đi qua bộ sưởi', 'start')
    d.call((120, 182), (40, 128), 'Cửa gió hồi / gió ngoài', 'start')
    d.call((540, 300), (620, 530), 'Cửa chọn hướng gió', 'end')
    info = [('Chức năng', 'Các cửa gió do mô-tơ nhỏ điều khiển: chọn gió ngoài / gió hồi, trộn gió lạnh với gió ấm để ra đúng nhiệt cài đặt, chọn hướng gió. Xe 2 vùng có cửa trộn riêng mỗi bên.'),
            ('Hay hỏng', ['Kẹt cửa, gãy bánh răng', 'Mô-tơ chấp hành hỏng']),
            ('Telemetry', ['Air Flow, Re-circulation (đã chọn)', 'Không có vị trí cửa gió thực'])]
    return reg(page(20, 'hop_hvac_cua_gio', 'Hộp HVAC – các cửa gió (mặt cắt)', 'HVAC module & air doors', 'sau taplo', 'gió cabin', d, info, ['air','cold','hot']))

def p21():
    d = D(); d.rect(150, 280, 140, 40, C['m2'], rx=4)
    for k in range(8): d.line((300 + k*12, 284), (306 + k*12, 316), C['m3'], sw=2)
    d.rect(290, 284, 100, 32, C['m1'], rx=2); d.path('M 390 290 L 470 296 L 470 304 L 390 310 Z', fill=C['m2'], stroke=C['m3'], sw=1)
    d.circ(462, 300, 7, C['hot'])
    d.rect(70, 270, 80, 60, C['dark2'], rx=6); d.rect(40, 286, 30, 10, '#C9A227', rx=2); d.rect(40, 304, 30, 10, '#C9A227', rx=2)
    d.path('M 0 0', stroke='none')
    d.call((462, 300), (500, 240), 'Hạt điện trở NTC\n(đổi điện trở theo nhiệt)', 'start')
    d.call((340, 300), (340, 400), 'Ren lắp vào ống / thân bộ phận')
    d.call((110, 300), (110, 400), 'Giắc 2 chân', 'middle')
    info = [('Chức năng', 'Đo nhiệt nước, gió, cell, motor… bằng điện trở NTC. Xe có hàng chục cảm biến; mọi quyết định bật / tắt của hệ nhiệt dựa vào chúng.'),
            ('Hay hỏng', ['Trôi / lệch dần (drift, offset)', 'Đứng giá trị (stuck)', 'Chân cắm ăn mòn → nhiễu']),
            ('Telemetry', ['Nhiệt nước vào / ra pin, cell, motor, EDS, dàn lạnh, cabin, ngoài trời', 'Cờ lỗi cảm biến: VCU Tsen, BMS, EDS']),
            ('Khi hỏng', 'Bộ điều khiển và thuật toán phía sau kết luận sai → lọc cảm biến trước.')]
    return reg(page(21, 'cam_bien_nhiet', 'Cảm biến nhiệt (NTC)', 'Temperature sensor', 'khắp hệ thống', 'đo lường', d, info, ['sig']))

def p22():
    d = D(); d.add('<polygon points="250,250 330,250 370,300 330,350 250,350 210,300" fill="#AEB8C2" stroke="#7E8A96" stroke-width="1.5"/>')
    d.rect(370, 270, 110, 60, C['dark2'], rx=8); d.rect(480, 284, 26, 32, C['dark'], rx=3)
    d.rect(150, 286, 60, 28, C['m1'], rx=2)
    for k in range(5): d.line((156 + k*11, 288), (162 + k*11, 312), C['m3'], sw=2)
    d.port((150, 300), (90, 300), C['hot'])
    d.call((290, 300), (290, 400), 'Thân lục giác')
    d.call((425, 300), (440, 220), 'Mạch đo (màng áp điện trở)', 'start')
    d.call((150, 300), (120, 220), 'Cổng van nạp\n(Schrader)', 'end')
    info = [('Chức năng', 'Đo áp suất gas phía cao áp / thấp áp để điều khiển máy nén, quạt và bảo vệ hệ thống.'),
            ('Hay hỏng', ['Trôi giá trị', 'Rò gas ở chân lắp']),
            ('Telemetry', ['KHÔNG có trong telemetry', 'Chỉ có “High pressure interlock failure” (Reserved)']),
            ('Ghi chú', 'Thiếu áp suất gas là lý do lớn nhất khiến khó phát hiện sớm rò gas (B7).')]
    return reg(page(22, 'cam_bien_ap_suat', 'Cảm biến áp suất gas', 'Refrigerant pressure transducer', 'đường gas cao / thấp áp', 'đo lường', d, info, ['hot']))

def p23():
    d = D(); d.cyl_h(60, 230, 300, 26, '#2B2F33', cap=False)
    d.rect(150, 196, 50, 68, '#C9D1D9', rx=6); d.rect(160, 190, 30, 12, '#AEB8C2', rx=3)
    d.rect(360, 200, 120, 60, C['m2'], rx=8); d.rect(480, 214, 80, 32, C['m1'], rx=4)
    d.ell(432, 230, 8, 30, '#E2552F', stroke='#9E2F18'); d.ell(452, 230, 8, 30, '#E2552F', stroke='#9E2F18')
    for k in range(5): d.circ(250 + k*18, 270 + k*16, 4, '#2FD3B8', stroke='#14A892')
    d.ell(330, 380, 70, 14, '#9FE0D3', stroke='#14A892')
    d.call((175, 230), (175, 128), 'Kẹp ống (lò xo / đai)')
    d.call((200, 230), (250, 160), 'Ống cao su EPDM', 'start')
    d.call((442, 230), (460, 140), 'O-ring trong đầu nối nhanh', 'start')
    d.call((290, 300), (40, 440), 'Điểm hay rò: kẹp lỏng,\nống nứt, O-ring lão hóa', 'start')
    info = [('Chức năng', 'Ống, kẹp, đầu nối nhanh và O-ring nối mọi bộ phận của vòng nước và vòng gas.'),
            ('Hay hỏng', ['Ống lão hóa nứt', 'Kẹp lỏng', 'O-ring chai cứng → rò nước / rò gas']),
            ('Telemetry', ['Gián tiếp: cờ thiếu nước, rò nước', 'Rò gas: chỉ thấy qua điều hòa yếu dần']),
            ('Ghi chú', 'Telemetry không chỉ ra được chỗ hở chính xác — xưởng phải dò.')]
    return reg(page(23, 'ong_kep_oring', 'Ống, kẹp ống, đầu nối & O-ring', 'Hoses, clamps, connectors & O-rings', 'khắp khoang trước, xuống pin', 'vòng nước / gas', d, info, ['batt']))

def p24():
    d = D(ox=320, oy=380); d.box(-140, -90, 0, 280, 190, 90, '#6B5B3E', op=0.35)
    d.cyl_v(230, 210, 32, 80, C['dark2']); d.cyl_v(330, 230, 32, 80, C['dark2'])
    d.rect(400, 260, 70, 26, '#E8E2CF', rx=4)
    d.line((150, 300), (230, 300), C['hv'], sw=8); d.line((262, 300), (330, 310), C['hv'], sw=8); d.line((362, 310), (400, 273), C['hv'], sw=8); d.line((470, 273), (540, 260), C['hv'], sw=8)
    d.rect(250, 330, 80, 18, C['m3'], rx=3)
    d.call((230, 230), (180, 140), 'Contactor (+ / −)', 'end')
    d.call((435, 273), (480, 200), 'Cầu chì chính', 'start')
    d.call((290, 339), (290, 470), 'Cảm biến dòng (shunt)')
    d.call((150, 300), (40, 380), 'Thanh cái cao áp', 'start')
    info = [('Chức năng', 'Hộp ngắt điện cao áp trong pin: đóng / ngắt pin với xe, chứa contactor, cầu chì, cảm biến dòng. Dòng lớn khi sạc nhanh làm BDU nóng.'),
            ('Hay hỏng', ['Tiếp điểm contactor nóng / hàn dính', 'Mối nối lỏng → nóng cục bộ']),
            ('Telemetry', ['BDU Temperature', 'BDU temperature warning, BDU hot']),
            ('Nguồn', 'VF 5: trong vỏ pin có BDU+, BDU−, cầu chì chính, cầu chì nổ (VATC).')]
    return reg(page(24, 'bdu', 'BDU – hộp ngắt cao áp', 'Battery disconnect unit', 'trong vỏ pin', 'điện cao áp', d, info, ['hv']))

def p25():
    d = D()
    def ecu(x, y, t, sub):
        d.rect(x, y, 130, 64, '#262B33', rx=8); d.rect(x+6, y+6, 118, 6, C['sig'], rx=3)
        d.text(x+65, y+36, t, 14, '#FFFFFF', 700); d.text(x+65, y+53, sub, 10, '#C9D3DC')
    ecu(60, 150, 'BMS', 'quản lý pin'); ecu(60, 260, 'EDS / MCU', 'trong inverter'); ecu(60, 370, 'CCU', 'điều hòa')
    ecu(260, 260, 'VCU', 'điều khiển xe'); ecu(460, 260, 'XGW', 'gateway'); ecu(460, 400, 'T-Box', 'gửi lên server')
    for y in (182, 292, 402): d.path(f'M 190 {y} L 225 {y} L 225 292 L 258 292', stroke=C['sig'], sw=2.5)
    d.flow((390, 292), (456, 292), C['sig']); d.flow((525, 324), (525, 396), C['sig'])
    d.path('M 125 150 L 125 120 L 525 120 L 525 256', stroke=C['sig'], sw=1.5, dash='4 4')
    d.text(330, 112, 'mạng CAN', 11, C['sig'], 600)
    d.call((325, 324), (330, 470), 'VCU ra lệnh bơm, quạt, van, PTC,\nmáy nén; tự đánh giá "error level"')
    info = [('Chức năng', 'Cảm biến → ECU đọc, lọc, tạo cờ → mạng CAN → gateway XGW → T-Box gửi lên server. Telemetry chỉ có những trường T-Box được cấu hình gửi.'),
            ('Hay hỏng', ['Mất giao tiếp (lost communication)', 'Phần mềm / hiệu chuẩn sai']),
            ('Telemetry', ['Telltale mất giao tiếp CCU, VCU, BMS', 'VCU … component error level']),
            ('Nguồn', 'VinFast: hệ nhiệt hiệu chuẩn qua VCU và CCU; VF 8 mới dùng máy tính trung tâm CVC.')]
    return reg(page(25, 'bo_dieu_khien', 'Bộ điều khiển & đường dữ liệu', 'ECUs & data path', 'cabin, trong pin, trên motor', 'điều khiển', d, info, ['sig']))

if __name__ == '__main__':
    for f in [p00, p01, p02, p03, p04, p05, p06, p07, p08, p09, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25]:
        f()
    print('\n'.join(os.path.basename(p) for p in PAGES))
