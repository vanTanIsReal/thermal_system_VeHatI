"""Giải bài A trên dữ liệu mô phỏng, theo 3 tầng:
   Tầng 1 – sạc chậm có do nhiệt không, mất bao nhiêu phút
   Tầng 2 – nếu do nhiệt, bộ phận nào đang yếu
   Tầng 3 – sức khỏe bộ phận đó trong tương lai (một xe bị rò gas chậm qua 12 tuần)
Thuật toán CHỈ đọc cột telemetry (content.*). Cột _truth_* chỉ dùng để chấm điểm.
Chạy:  python giai_bai_A.py      → in kết quả, ghi ket_qua.json và 3 biểu đồ .svg
"""
import json, os, glob
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
DT = 10.0                                    # giây / mẫu
T_NONG, T_LANH = 45.0, 20.0                  # BMS hãm khi cell lớn nhất > 45°C hoặc cell nhỏ nhất < 20°C

# ================================================================ đọc dữ liệu
def load(name):
    df = pd.read_csv(os.path.join(DATA, name + '.csv'), encoding='utf-8-sig', low_memory=False)
    ids = {c.split(' ')[0][len('content.'):]: c for c in df.columns if c.startswith('content.')}
    return df, ids

def sig(df, ids, rid, numeric=True):
    s = df[ids[rid]]
    return pd.to_numeric(s, errors='coerce').to_numpy(float) if numeric else s.astype(str).to_numpy()

def p_ref(soc_pct):
    """đường sạc chuẩn theo SOC (thông số hãng, kW)"""
    s = np.asarray(soc_pct) / 100.0
    return np.where(s < 0.5, 120.0, np.where(s < 0.8, 120 - (s - 0.5) / 0.3 * 70, np.maximum(15, 50 - (s - 0.8) / 0.15 * 35)))

def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            out.append((i, j)); i = j
        else: i += 1
    return out

# ================================================================ chỉ số của một phiên (tầng 1 + bằng chứng cho tầng 2)
def chi_so(name):
    df, ids = load(name)
    g = lambda rid: sig(df, ids, rid)
    P, I, V = g('34220.1.118'), np.abs(g('34220.1.59')), g('34220.1.60')
    Ireq, Iall, soc, chg = g('34220.1.76'), g('34220.1.106'), g('34183.1.9'), g('34193.1.5')
    Tmax, Tmin, Tin, Tout = g('34220.1.80'), g('34220.1.78'), g('34220.1.104'), g('34220.1.105')
    Qreq, pump, pre, Ta, Tev = g('34220.1.109'), g('34233.8.12'), g('34233.4.4'), g('34183.1.7'), g('34233.9.39')
    mode = sig(df, ids, '34184.1.5', numeric=False)
    flag = {k: bool(np.nanmax(g(rid)) > 0) for k, rid in
            [('quat', '34233.2.9'), ('may_nen', '34233.2.184'), ('thieu_nuoc', '34200.7.1'), ('van', '34233.2.11'), ('ptc', '34233.2.198')]}
    truth = str(df['_truth_faults'].dropna().iloc[-1]) if df['_truth_faults'].notna().any() else ''
    ses = runs((chg == 1) & (P > 1))
    if not ses: return None
    a0, b0 = max(ses, key=lambda r: r[1] - r[0]); sl = slice(a0, b0)
    m = np.zeros(len(P), bool); m[sl] = True
    Tbar, Tw = (Tmax + Tmin) / 2, (Tin + Tout) / 2

    # ---------------- TẦNG 1
    Pexp = p_ref(soc); Iref = Pexp * 1000 / V
    tram = (Ireq > 0) & (I < 0.9 * Ireq)                   # trạm không cấp đủ dòng BMS xin
    bms_han = ~tram & (Iall < 0.99 * Iref)                 # BMS cho phép ít hơn mức chuẩn ở SOC đó
    nong, lanh = Tmax > T_NONG, Tmin < T_LANH
    han_nhiet = bms_han & (nong | lanh) & m
    r = P / Pexp
    mat = np.where(han_nhiet & (r < 1), DT * (1 - r), 0.0)
    dai = max([b - a for a, b in runs(han_nhiet & (r < 0.85))] or [0])
    t1 = {'cham_do_nhiet': bool(dai * DT >= 120),
          'phut_mat': round(float(mat.sum()) / 60, 1),
          'phut_mat_nong': round(float(mat[nong & ~lanh].sum()) / 60, 1), 'phut_mat_lanh': round(float(mat[lanh].sum()) / 60, 1),
          'ty_le_cong_suat_thap_nhat': round(float(np.nanmin(r[sl])), 2),
          'thoi_gian_sac_phut': round((b0 - a0) * DT / 60, 1), 'soc': [round(float(soc[a0])), round(float(soc[b0 - 1]))],
          'cell_max_dau': round(float(Tmax[a0]), 1), 'cell_max_dinh': round(float(np.nanmax(Tmax[sl])), 1),
          'cell_min_dau': round(float(Tmin[a0]), 1), 'T_ngoai': round(float(np.mean(Ta[sl])), 1)}
    t1['ly_do'] = ('pin_lanh' if t1['phut_mat_lanh'] > t1['phut_mat_nong'] else 'pin_nong') if t1['phut_mat'] > 0 else \
                  ('tram_sac' if np.mean(tram[sl]) > 0.3 else 'khong_bi_han')

    # ---------------- bằng chứng hệ tản (tầng 2)
    cool = (Qreq > 0.05) & (pump == 1)
    cm = np.zeros_like(cool)
    for a, b in runs(cool): cm[min(b, a + 30):b] = True        # bỏ 5 phút đầu mỗi đoạn làm mát
    cm &= m
    ev = {}
    if cm.sum() >= 6:
        ev['do_lanh_nuoc_c'] = round(float(np.median(Tmax[cm] - Tin[cm])), 2)      # nước đủ lạnh không
        ev['nuoc_ra_tru_vao_c'] = round(float(np.median(Tout[cm] - Tin[cm])), 2)   # nước chảy đủ không
        ev['nuoc_vao_cao_hon_ra'] = bool(np.median(Tin[cm] - Tout[cm]) > 1.0)      # vô lý khi đang làm mát → cảm biến
    ev['bom_tat_khi_can'] = bool(np.sum((Qreq > 0.05) & (pump == 0) & m) >= 6)
    # cân bằng nhiệt trong phiên: dT̄/dt = a·I² − k·(T̄ − T_nước) − b·(T̄ − T_ngoài)
    y = np.gradient(Tbar[sl]) * (60 / DT)
    X = np.c_[(I[sl] / 1000) ** 2, -(Tbar[sl] - Tw[sl]), -(Tbar[sl] - Ta[sl])]
    keep = np.zeros(b0 - a0, bool); keep[3:-3] = True
    keep &= ~np.isnan(y) & ~np.isnan(X).any(1)
    if keep.sum() > 30:
        coef = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
        if coef[2] < 0: coef = np.r_[np.linalg.lstsq(X[keep][:, :2], y[keep], rcond=None)[0], 0.0]
        pred = X[keep] @ coef
        ev.update({'a': round(float(coef[0]), 2), 'k': round(float(coef[1]), 4), 'b': round(float(coef[2]), 4),
                   'R2': round(float(1 - np.sum((y[keep] - pred) ** 2) / np.sum((y[keep] - y[keep].mean()) ** 2)), 3)})
        Im = float(np.mean(I[sl])) / 1000; Twm = float(np.median(Tw[cm])) if cm.any() else float(np.mean(Tw[sl]))
        a_, k_, b_ = coef
        ev['nhiet_can_bang_du_kien_c'] = round(float((a_ * Im ** 2 + k_ * Twm + b_ * float(np.mean(Ta[sl]))) / (k_ + b_)), 1) if k_ + b_ > 1e-6 else None
    ac = np.array([x == 'cool' for x in mode]); ac_on = np.zeros_like(ac)
    for a, b in runs(ac): ac_on[min(b, a + 60):b] = True     # điều hòa cabin đã chạy ≥ 10 phút
    ev['dan_lanh_tb_c'] = round(float(np.median(Tev[ac_on])), 1) if ac_on.sum() >= 6 else None
    ev['co_loi'] = [k for k, v in flag.items() if v]
    ev['lam_am_truoc'] = bool(np.nanmax(pre[:b0]) > 0)
    warm = (pre > 0)
    ev['nuoc_am_hon_pin_khi_lam_am'] = bool(np.any((Tin - Tbar)[warm] >= 3)) if warm.any() else None
    return {'ten': name, 'su_that': truth, 'tang1': t1, 'bang_chung': ev, 'flag': flag,
            '_s': {'t': (np.arange(b0 - a0) * DT / 60).tolist(), 'P': P[sl].tolist(), 'Pexp': Pexp[sl].tolist(),
                   'Tmax': Tmax[sl].tolist(), 'Tin': Tin[sl].tolist()}}

# ================================================================ "mức đáng lẽ phải có" học từ xe khỏe
def hoc_xe_khoe(res):
    kh = [r for n, r in res.items() if n.startswith('khoe_')]
    A = np.array([[1, r['tang1']['T_ngoai'], r['tang1']['cell_max_dau']] for r in kh])
    y = np.array([r['bang_chung']['do_lanh_nuoc_c'] for r in kh])
    c = np.linalg.lstsq(A, y, rcond=None)[0]
    resid = y - A @ c
    flow = np.array([r['bang_chung']['nuoc_ra_tru_vao_c'] for r in kh])
    kk = np.array([r['bang_chung']['k'] for r in kh])
    return {'do_lanh_nuoc': {'he_so [c0, c·T_ngoai, c·cell_dau]': [round(float(v), 3) for v in c],
                             'sai_so_chuan_c': round(float(np.std(resid, ddof=3)), 2)},
            'nuoc_ra_tru_vao_c': {'trung_vi': round(float(np.median(flow)), 2), 'lon_nhat': round(float(flow.max()), 2)},
            'k': {'trung_vi': round(float(np.median(kk)), 4), 'nho_nhat': round(float(kk.min()), 4)},
            '_c': c.tolist(), 'so_phien': len(kh)}

def du_kien_do_lanh(base, t1):
    c = base['_c']; return c[0] + c[1] * t1['T_ngoai'] + c[2] * t1['cell_max_dau']

# ================================================================ TẦNG 2: khâu kém → bộ phận nghi
def chan_doan(r, base):
    ev, t1, fl = r['bang_chung'], r['tang1'], r['flag']
    H = None
    if 'do_lanh_nuoc_c' in ev:
        H = ev['do_lanh_nuoc_c'] / du_kien_do_lanh(base, t1)            # sức khỏe nguồn lạnh của phiên
    Hk = (ev.get('k') or np.nan) / base['k']['trung_vi']                 # sức khỏe dòng nước / tấm làm mát
    flow_hi = ev.get('nuoc_ra_tru_vao_c', 0) > 1.4 * base['nuoc_ra_tru_vao_c']['lon_nhat']
    if ev.get('nuoc_vao_cao_hon_ra'):           khau = 'cam_bien_nghi_sai'
    elif t1['ly_do'] == 'pin_lanh':
        khau = 'khong_lam_am_truoc' if not ev['lam_am_truoc'] else ('lam_am_kem' if not ev['nuoc_am_hon_pin_khi_lam_am'] else 'binh_thuong')
    elif ev.get('bom_tat_khi_can'):             khau = 'khong_phan_ung'
    elif flow_hi or Hk < 0.6:                   khau = 'nuoc_chay_kem'
    elif H is not None and H < 0.8:             khau = 'nuoc_khong_du_lanh'
    else:                                       khau = 'binh_thuong'
    dl_am = ev.get('dan_lanh_tb_c') is not None and ev['dan_lanh_tb_c'] > 10
    if khau == 'nuoc_khong_du_lanh':
        if fl['van']:               bp = [('van_4_nga', .6), ('chiller_hoac_van_chiller', .25), ('thieu_gas', .15)]
        elif fl['may_nen']:         bp = [('may_nen', .7), ('thieu_gas', .2), ('chiller_hoac_van_chiller', .1)]
        elif fl['quat']:            bp = [('quat_ket', .7), ('thieu_gas', .15), ('chiller_hoac_van_chiller', .15)]
        elif dl_am:                 bp = [('thieu_gas', .65), ('may_nen', .2), ('quat_ket', .15)]
        else:                       bp = [('chiller_hoac_van_chiller', .6), ('thieu_gas', .2), ('quat_ket', .2)]
    elif khau == 'nuoc_chay_kem':   bp = [('thieu_nuoc', .7), ('bom_pin', .3)] if fl['thieu_nuoc'] else [('bom_pin', .7), ('thieu_nuoc', .3)]
    elif khau == 'lam_am_kem':      bp = [('ptc_nuoc', .8 if fl['ptc'] else .6)]
    elif khau == 'khong_phan_ung':  bp = [('dieu_khien_bom', .5)]
    elif khau == 'cam_bien_nghi_sai': bp = [('cam_bien_nuoc_vao_pin', .8)]
    elif fl['van'] and t1['phut_mat'] > 0: bp = [('van_4_nga', .5)]
    else:                           bp = []
    return {'khau_kem': khau, 'bo_phan_nghi': [{'bo_phan': b, 'p': p} for b, p in bp],
            'suc_khoe_nguon_lanh': None if H is None else round(float(H), 2), 'suc_khoe_dong_nuoc_k': round(float(Hk), 2)}

# ================================================================ TẦNG 3: sức khỏe theo tuần + dự báo
def theil_sen(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    s = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if x[j] != x[i]]
    sl = float(np.median(s)) if s else 0.0
    return sl, float(np.median(y - sl * x))

def tang3(res, base, NGUONG_PHUT=5.0):
    # ngưỡng nguy hiểm: phiên chuẩn nặng, gas giảm dần → sức khỏe đo được ở mức nào thì mất > NGUONG_PHUT phút
    std = []
    for gas in range(100, 45, -5):
        r = res[f'chuan_gas_{gas}']
        std.append({'gas_that': gas, 'suc_khoe': r['tang2']['suc_khoe_nguon_lanh'], 'phut_mat': r['tang1']['phut_mat']})
    H = np.array([s['suc_khoe'] for s in std]); M = np.array([s['phut_mat'] for s in std]); G = np.array([s['gas_that'] for s in std])
    H_crit = float(np.interp(NGUONG_PHUT, M, H)) if M.max() >= NGUONG_PHUT else None
    gas_crit = float(np.interp(NGUONG_PHUT, M, G)) if M.max() >= NGUONG_PHUT else None
    truth = json.load(open(os.path.join(DATA, 'tuan_su_that.json'), encoding='utf-8'))
    weeks = []
    for w in truth:
        r = res[f"tuan_{w['tuan']:02d}"]
        weeks.append({'tuan': w['tuan'], 'gas_that': w['gas_that'], 'T_ngoai': r['tang1']['T_ngoai'], 'cell_dau': r['tang1']['cell_max_dau'],
                      'do_lanh_nuoc_c': r['bang_chung']['do_lanh_nuoc_c'], 'du_kien_c': round(du_kien_do_lanh(base, r['tang1']), 2),
                      'suc_khoe': r['tang2']['suc_khoe_nguon_lanh'], 'phut_mat': r['tang1']['phut_mat'],
                      'khau_kem': r['tang2']['khau_kem'],
                      'bo_phan_1': (r['tang2']['bo_phan_nghi'] or [{'bo_phan': '—'}])[0]['bo_phan']})
    tuan_that = None if gas_crit is None else 1 + (100 - gas_crit) / 4      # gas giảm 4%/tuần
    rng = np.random.default_rng(0); fc = []
    for n in range(4, len(weeks) + 1):
        x = np.array([w['tuan'] for w in weeks[:n]], float); y = np.array([w['suc_khoe'] for w in weeks[:n]], float)
        sl, ic = theil_sen(x, y); H_now = ic + sl * n
        eta = (H_now - H_crit) / -sl if (H_crit is not None and sl < -1e-3) else None
        bs = []
        for _ in range(400):
            idx = rng.integers(0, n, n)
            if len(set(x[idx])) < 3: continue
            s2, i2 = theil_sen(x[idx], y[idx])
            if s2 < -1e-3 and H_crit is not None: bs.append(n + ((i2 + s2 * n) - H_crit) / -s2)
        lo, hi = (np.percentile(bs, [10, 90]) if len(bs) > 50 else (None, None))
        # cách 2: chỉ dùng 5 tuần gần nhất (bắt được kiểu "giảm nhanh dần")
        xg, yg = x[-5:], y[-5:]; slg, icg = theil_sen(xg, yg); Hg = icg + slg * n
        etag = (Hg - H_crit) / -slg if (H_crit is not None and slg < -1e-3) else None
        fc.append({'dung_o_tuan': n, 'suc_khoe_hien_tai': round(H_now, 3), 'giam_moi_tuan': round(-sl, 4),
                   'gan_day_giam_moi_tuan': round(-slg, 4),
                   'gan_day_du_bao_cham_nguong_o_tuan': None if etag is None else round(n + max(etag, 0), 1),
                   'con_khoang_tuan': None if eta is None else round(max(eta, 0), 1),
                   'du_bao_cham_nguong_o_tuan': None if eta is None else round(n + max(eta, 0), 1),
                   'khoang_10_90_tuan': None if lo is None else [round(float(lo), 1), round(float(hi), 1)]})
    return {'nguong_phut': NGUONG_PHUT, 'suc_khoe_nguy_hiem': None if H_crit is None else round(H_crit, 3),
            'gas_nguy_hiem_that': None if gas_crit is None else round(gas_crit, 1), 'phien_chuan': std,
            'tuan': weeks, 'tuan_that_su_cham_nguong': None if tuan_that is None else round(tuan_that, 1), 'du_bao': fc}

# ================================================================ biểu đồ SVG
INK, MUTED, GRID, BG = '#1f2328', '#59636e', '#d8dee4', '#ffffff'

def nice_ticks(lo, hi, n=5):
    step = (hi - lo) / max(1, n); mag = 10 ** np.floor(np.log10(step)); f = step / mag
    step = (1 if f < 1.5 else 2 if f < 3 else 5 if f < 7 else 10) * mag
    return np.arange(np.ceil(lo / step) * step, hi + step * 1e-9, step)
S1, S2 = '#2a78d6', '#eb6834'

def svg_chart(path, title, series, xlab, ylab, w=680, h=320, refs=(), vlines=(), points=(), ylim=None):
    L, R, T, B = 52, 16, 48, 40
    xs = np.concatenate([np.asarray(s['x'], float) for s in series] + [np.asarray(p['x'], float) for p in points] + [np.asarray([v['x'] for v in vlines], float)])
    ys = np.concatenate([np.asarray(s['y'], float) for s in series] + [np.asarray(p['y'], float) for p in points] + [np.asarray([r['y'] for r in refs], float)])
    xs, ys = xs[~np.isnan(xs)], ys[~np.isnan(ys)]
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = ylim if ylim else (float(ys.min()), float(ys.max()))
    if not ylim: pad = (y1 - y0) * 0.08 or 1; y0 -= pad; y1 += pad
    X = lambda v: L + (v - x0) / (x1 - x0 or 1) * (w - L - R)
    Y = lambda v: h - B - (v - y0) / (y1 - y0) * (h - T - B)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Segoe UI, Arial, sans-serif">',
         f'<rect width="{w}" height="{h}" fill="{BG}"/>', f'<text x="{L}" y="18" font-size="14" font-weight="600" fill="{INK}">{title}</text>']
    fmt = (lambda t: f'{t:.0f}') if (y1 - y0) > 4 else (lambda t: f'{t:.1f}')
    for t in nice_ticks(y0, y1):
        o += [f'<line x1="{L}" x2="{w-R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRID}"/>',
              f'<text x="{L-6}" y="{Y(t)+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{fmt(t)}</text>']
    for t in nice_ticks(x0, x1, 7):
        o.append(f'<text x="{X(t):.1f}" y="{h-B+16}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:.0f}</text>')
    o += [f'<text x="{(L+w-R)/2}" y="{h-6}" font-size="11" fill="{MUTED}" text-anchor="middle">{xlab}</text>',
          f'<text x="12" y="{(T+h-B)/2}" font-size="11" fill="{MUTED}" text-anchor="middle" transform="rotate(-90 12 {(T+h-B)/2})">{ylab}</text>']
    for r in refs:
        o += [f'<line x1="{L}" x2="{w-R}" y1="{Y(r["y"]):.1f}" y2="{Y(r["y"]):.1f}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 4"/>',
              f'<text x="{w-R-4}" y="{Y(r["y"])-5:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{r["label"]}</text>']
    for v in vlines:
        o += [f'<line x1="{X(v["x"]):.1f}" x2="{X(v["x"]):.1f}" y1="{T}" y2="{h-B}" stroke="{MUTED}" stroke-dasharray="3 3"/>',
              f'<text x="{X(v["x"])+4:.1f}" y="{T+12 + v.get("dy", 0)}" font-size="11" fill="{MUTED}">{v["label"]}</text>']
    for s in series:
        pts = [(X(a), Y(b)) for a, b in zip(s['x'], s['y']) if not (np.isnan(a) or np.isnan(b))]
        dash = ' stroke-dasharray="6 4"' if s.get('dash') else ''
        o.append(f'<path d="M{" L".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{s["c"]}" stroke-width="2"{dash} stroke-linejoin="round"/>')
    for p in points:
        for a, b in zip(p['x'], p['y']):
            o.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="4.5" fill="{p["c"]}" stroke="{BG}" stroke-width="2"/>')
    lx, ly = L, 32
    for s in list(series) + list(points):
        if not s.get('label'): continue
        wlab = 26 + 6.3 * len(s['label'])
        if lx + wlab > w - R: lx, ly = L, ly + 14
        if s in points: o.append(f'<circle cx="{lx+6}" cy="{ly-3}" r="4" fill="{s["c"]}"/>')
        else: o.append(f'<line x1="{lx}" x2="{lx+14}" y1="{ly-3}" y2="{ly-3}" stroke="{s["c"]}" stroke-width="2"{" stroke-dasharray=\"4 3\"" if s.get("dash") else ""}/>')
        o.append(f'<text x="{lx+18}" y="{ly+1}" font-size="11" fill="{INK}">{s["label"]}</text>')
        lx += wlab
    o.append('</svg>')
    open(path, 'w', encoding='utf-8').write('\n'.join(o))

# ================================================================ chạy
if __name__ == '__main__':
    names = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DATA, '*.csv')))
    res = {n: chi_so(n) for n in names}
    base = hoc_xe_khoe(res)
    for r in res.values(): r['tang2'] = chan_doan(r, base)
    t3 = tang3(res, base)

    print('=== MỨC ĐÁNG LẼ (học từ', base['so_phien'], 'phiên xe khỏe) ===')
    print('độ lạnh của nước =', base['do_lanh_nuoc'], '| nước ra−vào', base['nuoc_ra_tru_vao_c'], '| k', base['k'])
    print('\n=== TẦNG 1 + 2: các ca lỗi riêng lẻ ===')
    print(f"{'ca':19}{'sự thật':15}{'chậm?':6}{'lý do':13}{'phút':6}{'cell đỉnh':10}{'khâu kém':20}{'bộ phận #1':27}{'SK lạnh':8}{'SK k':6}{'ra−vào':7}{'k':8}{'a':7}{'dàn lạnh':8}")
    for n in names:
        if n.startswith(('khoe_', 'tuan_', 'chuan_')): continue
        r = res[n]; e = r['bang_chung']; t1 = r['tang1']; t2 = r['tang2']
        b1 = t2['bo_phan_nghi'][0] if t2['bo_phan_nghi'] else {'bo_phan': '—', 'p': ''}
        print(f"{n:19}{r['su_that'][:14]:15}{('có' if t1['cham_do_nhiet'] else '—'):6}{t1['ly_do']:13}{t1['phut_mat']:<6}{t1['cell_max_dinh']:<10}"
              f"{t2['khau_kem']:20}{(b1['bo_phan'] + ' ' + str(b1['p'])):27}{str(t2['suc_khoe_nguon_lanh']):8}{str(t2['suc_khoe_dong_nuoc_k']):6}"
              f"{str(e.get('nuoc_ra_tru_vao_c')):7}{str(e.get('k')):8}{str(e.get('a')):7}{str(e.get('dan_lanh_tb_c')):8}")
    print('\n=== TẦNG 3: xe bị rò gas chậm ===')
    print('ngưỡng: mất >', t3['nguong_phut'], 'phút ở phiên chuẩn nặng ⇔ sức khỏe <', t3['suc_khoe_nguy_hiem'],
          '⇔ gas thật <', t3['gas_nguy_hiem_that'], '% → thực tế chạm ở tuần', t3['tuan_that_su_cham_nguong'])
    for s in t3['phien_chuan']: print('   phiên chuẩn: gas', s['gas_that'], '% → sức khỏe', s['suc_khoe'], ', mất', s['phut_mat'], 'phút')
    for w in t3['tuan']:
        print(f"tuần {w['tuan']:2}  gas thật {w['gas_that']:3}%  T_ngoài {w['T_ngoai']:4}  cell đầu {w['cell_dau']:4}  độ lạnh {w['do_lanh_nuoc_c']:5} (đáng lẽ {w['du_kien_c']:5})  sức khỏe {w['suc_khoe']:.2f}  mất {w['phut_mat']:4} phút  {w['khau_kem']:20} {w['bo_phan_1']}")
    for f in t3['du_bao']:
        print(f"đứng ở tuần {f['dung_o_tuan']:2}: [mọi tuần] giảm {f['giam_moi_tuan']*100:.1f}%/tuần → chạm ngưỡng tuần {f['du_bao_cham_nguong_o_tuan']} (khoảng {f['khoang_10_90_tuan']})"
              f"   |   [5 tuần gần nhất] giảm {f['gan_day_giam_moi_tuan']*100:.1f}%/tuần → chạm ngưỡng tuần {f['gan_day_du_bao_cham_nguong_o_tuan']}")

    # ---------- biểu đồ
    k, c = res['hcm_khoe']['_s'], res['hcm_gas_65']['_s']
    svg_chart(os.path.join(HERE, 'bd1_cong_suat_sac.svg'), 'Công suất sạc trong phiên chuẩn nặng (kW)',
              [{'x': k['t'], 'y': k['P'], 'c': S1, 'label': 'Xe khỏe'}, {'x': c['t'], 'y': c['P'], 'c': S2, 'label': 'Gas còn 65%'},
               {'x': k['t'], 'y': k['Pexp'], 'c': MUTED, 'dash': True, 'label': 'Đường chuẩn ở cùng SOC (xe khỏe)'}],
              'phút từ lúc cắm sạc', 'kW')
    svg_chart(os.path.join(HERE, 'bd2_nhiet_pin_va_nuoc_vao.svg'), 'Nhiệt cell lớn nhất và nhiệt nước vào pin (°C)',
              [{'x': k['t'], 'y': k['Tmax'], 'c': S1, 'label': 'Cell – xe khỏe'}, {'x': c['t'], 'y': c['Tmax'], 'c': S2, 'label': 'Cell – gas 65%'},
               {'x': k['t'], 'y': k['Tin'], 'c': S1, 'dash': True, 'label': 'Nước vào – xe khỏe'}, {'x': c['t'], 'y': c['Tin'], 'c': S2, 'dash': True, 'label': 'Nước vào – gas 65%'}],
              'phút từ lúc cắm sạc', '°C', refs=[{'y': 45, 'label': 'BMS bắt đầu hãm sạc (45°C)'}])
    W = t3['tuan']; n0 = 8; f = [x for x in t3['du_bao'] if x['dung_o_tuan'] == n0][0]
    xs = np.array([w['tuan'] for w in W[:n0]], float); ys = np.array([w['suc_khoe'] for w in W[:n0]], float)
    sl, ic = theil_sen(xs, ys); end = 16.0; xf = np.linspace(1, end, 30)
    slg, icg = theil_sen(xs[-5:], ys[-5:]); xg = np.linspace(4, end, 20)
    vl = [{'x': n0, 'label': 'hôm nay (tuần 8)'}]
    if t3['tuan_that_su_cham_nguong']: vl.append({'x': t3['tuan_that_su_cham_nguong'], 'label': 'thực tế chạm ngưỡng', 'dy': 16})
    svg_chart(os.path.join(HERE, 'bd3_suc_khoe_theo_tuan.svg'), 'Sức khỏe nguồn lạnh theo tuần – xe bị rò gas chậm',
              [{'x': xf.tolist(), 'y': (ic + sl * xf).tolist(), 'c': S1, 'dash': True, 'label': 'Xu hướng mọi tuần (1–8)'},
               {'x': xg.tolist(), 'y': (icg + slg * xg).tolist(), 'c': S2, 'dash': True, 'label': 'Xu hướng 5 tuần gần nhất (4–8)'}],
              'tuần', 'sức khỏe (1 = như xe khỏe)', ylim=(0.3, 1.15),
              refs=[{'y': t3['suc_khoe_nguy_hiem'], 'label': f"ngưỡng nguy hiểm {t3['suc_khoe_nguy_hiem']:.2f}"}] if t3['suc_khoe_nguy_hiem'] else [],
              vlines=vl,
              points=[{'x': [w['tuan'] for w in W[:n0]], 'y': [w['suc_khoe'] for w in W[:n0]], 'c': S1, 'label': 'Đã đo (tuần 1–8)'},
                      {'x': [w['tuan'] for w in W[n0:]], 'y': [w['suc_khoe'] for w in W[n0:]], 'c': MUTED, 'label': 'Đo sau đó (tuần 9–12)'}])
    out = {n: {k2: v for k2, v in r.items() if k2 != '_s'} for n, r in res.items()}
    out['_xe_khoe'] = {k2: v for k2, v in base.items() if k2 != '_c'}; out['_tang3'] = t3
    json.dump(out, open(os.path.join(HERE, 'ket_qua.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\nĐã ghi ket_qua.json và 3 biểu đồ .svg')
