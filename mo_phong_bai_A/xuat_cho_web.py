"""Xuất kết quả bài A (10 ca, mô hình xe khỏe, 12 tuần rò gas) ra bai_A_web.json để nhúng vào trang 3D."""
import json, os, glob
import numpy as np
import giai_bai_A as G

HERE = os.path.dirname(os.path.abspath(__file__))
names = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(G.DATA, '*.csv')))
res = {n: G.chi_so(n) for n in names}
base = G.hoc_xe_khoe(res)
for r in res.values(): r['tang2'] = G.chan_doan(r, base)
t3 = G.tang3(res, base)
for st in t3['phien_chuan']: st['do_lanh_nuoc_c'] = res[f"chuan_gas_{st['gas_that']}"]['bang_chung']['do_lanh_nuoc_c']

LABEL = {'hcm_khoe': 'Xe khỏe', 'hcm_chiller_50': 'Chiller còn 50%', 'hcm_chiller_15': 'Chiller còn 15%',
         'hcm_gas_65': 'Gas còn 65%', 'hcm_quat_chet': 'Quạt két chết', 'hcm_bom_pin_40': 'Bơm pin còn 40%',
         'hcm_van_ket': 'Van 4 ngả kẹt', 'hcm_cam_bien_lech': 'Cảm biến nước vào lệch +6°C',
         'hn_khoe': 'Mùa đông – xe khỏe', 'hn_ptc_hong': 'Mùa đông – PTC hỏng'}
r1 = lambda v: None if v is None else round(float(v), 2)

def series(name, step=2):
    df, ids = G.load(name)
    g = lambda rid: G.sig(df, ids, rid)
    P, soc, chg = g('34220.1.118'), g('34183.1.9'), g('34193.1.5')
    a0, b0 = max(G.runs((chg == 1) & (P > 1)), key=lambda r: r[1] - r[0])
    sl = slice(a0, b0, step)
    return {'t': [round(i * G.DT / 60, 2) for i in range(0, b0 - a0, step)], 'P': [r1(v) for v in P[sl]],
            'Pexp': [r1(v) for v in G.p_ref(soc[sl])], 'Tmax': [r1(v) for v in g('34220.1.80')[sl]],
            'Tin': [r1(v) for v in g('34220.1.104')[sl]], 'Tout': [r1(v) for v in g('34220.1.105')[sl]]}

cases = []
for n in LABEL:
    r = res[n]
    cases.append({'id': n, 'ten': LABEL[n], 'su_that': r['su_that'], 'mua': 'dong' if n.startswith('hn') else 'he',
                  'tang1': r['tang1'], 'tang2': r['tang2'], 'bang_chung': r['bang_chung'],
                  'do_lanh_dang_le': r1(G.du_kien_do_lanh(base, r['tang1'])) if 'do_lanh_nuoc_c' in r['bang_chung'] else None,
                  'series': series(n)})
kh = [res[n] for n in names if n.startswith('khoe_')]
train = [{'Ta': r['tang1']['T_ngoai'], 'cell_dau': r['tang1']['cell_max_dau'], 'thuc_te': r['bang_chung']['do_lanh_nuoc_c'],
          'du_doan': r1(G.du_kien_do_lanh(base, r['tang1']))} for r in kh]
out = {'mo_hinh': {'he_so': [round(v, 4) for v in base['_c']], 'sai_so_chuan_c': base['do_lanh_nuoc']['sai_so_chuan_c'],
                   'nuoc_ra_tru_vao_c': base['nuoc_ra_tru_vao_c'], 'k': base['k'], 'so_phien': base['so_phien'], 'du_lieu_hoc': train},
       'cases': cases,
       'tang3': {k: v for k, v in t3.items()}}
json.dump(out, open(os.path.join(HERE, 'bai_A_web.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', os.path.getsize(os.path.join(HERE, 'bai_A_web.json')) // 1024, 'KB')
