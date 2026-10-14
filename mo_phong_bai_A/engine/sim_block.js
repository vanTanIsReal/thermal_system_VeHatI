/* ================================================================== FAULT DETECTORS
   Mỗi bộ phát hiện chỉ đọc giá trị TELEMETRY (qua SIM_GEN, đúng như cột CSV), không đọc cột _truth_.
   Ngưỡng chọn từ chạy hiệu chuẩn trên mô phỏng (xe khỏe vs xe lỗi) — là baseline luật, chưa phải mô hình học máy. */
const tv = (r, id)=>{ const v = SIM_GEN[id][1](r); return typeof v==='number' ? v : v; };
const tn = (r, id)=> +SIM_GEN[id][1](r);
const lastRows = (H, sec)=> H.slice(-Math.max(1, Math.round(sec/10)));
const mean = a=> a.reduce((x,y)=>x+y, 0)/Math.max(1, a.length);
const f1 = v=> (Math.round(v*10)/10).toFixed(1);
const DET = [
  {id:'d1', bai:'1', name:'Rò / thiếu nước làm mát', comp:'tank', chart:'cb', faults:['leak'],
   run(r){ if(tn(r,'34200.7.1')) return [2, 'Cờ thiếu nước làm mát (34200.7.1) đang bật'];
           return [0, 'Chưa có cờ thiếu nước. Telemetry chỉ có cờ, không có giá trị mức nước, nên chỉ biết khi mức đã xuống thấp']; }},
  {id:'d5', bai:'B5', name:'Cảm biến nhiệt lệch', comp:'sensors', chart:'cb', faults:['offset'],
   run(r, H){
     if(tn(r,'34183.1.30') >= 360){
       const o = [tn(r,'34220.1.80'), tn(r,'34220.1.78'), tn(r,'34220.1.105'), tn(r,'34220.1.3')].sort((a,b)=>a-b), med = (o[1]+o[2])/2;
       const d = tn(r,'34220.1.104') - med;
       return Math.abs(d) > 3 ? [2, `Đỗ nguội ${Math.round(tn(r,'34183.1.30')/60)} giờ: nước vào pin ${f1(tn(r,'34220.1.104'))}°C lệch ${f1(d)}°C so với trung vị các cảm biến pin (${f1(med)}°C)`]
                              : [0, `Đỗ nguội: các cảm biến pin khớp nhau (lệch ${f1(d)}°C)`];
     }
     const w = lastRows(H, 300);
     const quiet = w.length>=30 && w.every(x=>tn(x,'34183.1.10')===1 && tn(x,'34233.8.12')===1 && tn(x,'34220.1.109')===0 && tn(x,'34193.1.5')===0 && tn(x,'34233.4.4')===0);
     if(!quiet) return null;
     const d = mean(w.map(x=>Math.abs(tn(x,'34220.1.104')-tn(x,'34220.1.105'))));
     return d > 3.5 ? [2, `Khi chạy, bơm pin chạy mà pin không trao đổi nhiệt: nước vào và ra pin lệch ${f1(d)}°C trong 5 phút (bình thường < 1°C)`]
                    : [0, `Nước vào / ra pin khớp nhau khi pin không trao đổi nhiệt (${f1(d)}°C)`];
   }},
  {id:'d6', bai:'B6', name:'Làm mát pin kém', comp:'chiller', chart:'cb', faults:['chiller','pump','gas','fan','valve','leak'],
   run(r, H){
     const w = lastRows(H, 300);
     if(w.length<30 || !w.every(x=>tn(x,'34220.1.109')>1)) return null;
     if(DET_ST.d5 && DET_ST.d5.alarm!==null) return [0, 'Bỏ qua: cảm biến nước vào pin đang bị nghi lệch (B5) nên chưa kết luận được']; 
     const gap = mean(w.map(x=>tn(x,'34220.1.80')-tn(x,'34220.1.104'))), dtw = mean(w.map(x=>tn(x,'34220.1.105')-tn(x,'34220.1.104')));
     if(dtw > 4.5) return [2, `BMS yêu cầu làm mát 5 phút; nước ra – vào pin chênh ${f1(dtw)}°C → lưu lượng thấp (nghi bơm yếu / thiếu nước)`];
     if(gap < 6) return [2, `BMS yêu cầu làm mát 5 phút nhưng nước vào pin chỉ thấp hơn cell ${f1(gap)}°C (xe khỏe ≥ 7°C) → chiller không kéo được nhiệt (nghi chiller / thiếu gas / quạt két)`];
     return [0, `Chiller kéo nước vào pin thấp hơn cell ${f1(gap)}°C — bình thường`];
   }},
  {id:'d3', bai:'3 · 4', name:'Điều hòa kém lạnh + kiểu hỏng', comp:'evaporator', chart:'cc', faults:['gas','fan'],
   run(r, H){
     const w = lastRows(H, 600);
     if(w.length<60 || !w.every(x=>tv(x,'34184.1.5')==='cool' && tn(x,'34184.1.25')>0)) return null;
     const demand = mean(w.map(x=>tn(x,'34183.1.15')-tn(x,'34184.1.6')));
     if(demand < 2) return [0, `Cabin đã gần nhiệt cài đặt (cao hơn ${f1(demand)}°C) — điều hòa chạy nhẹ, chưa đủ tải để đánh giá`];
     const w3 = lastRows(H, 180), ev = mean(w3.map(x=>tn(x,'34233.9.39')));
     if(ev <= 10) return [0, `Dàn lạnh trung bình 3 phút ${f1(ev)}°C — bình thường (xe khỏe ≤ 8°C)`];
     const moving = w.filter(x=>tn(x,'34183.1.2')>20), movingPoor = moving.length>6 && mean(moving.map(x=>tn(x,'34233.9.39')))>10;
     const cause = tn(r,'34233.2.9')>0 ? 'quạt két hỏng (VCU báo lỗi quạt)' : movingPoor ? 'thiếu gas / máy nén yếu (kém cả khi xe chạy)' : 'thiếu gas nhẹ hoặc dàn nóng bẩn (chỉ kém khi xe đứng)';
     return [2, `AC bật hơn 10 phút mà dàn lạnh trung bình ${f1(ev)}°C → kém lạnh. Kiểu hỏng: ${cause}`];
   }},
  {id:'d9', bai:'B9', name:'Sạc nhanh chậm vì nhiệt', comp:'battery', chart:'cp', truth:r=>r.phase==='charge' && r.Pch>0 && r.fT<0.85,
   run(r, H){
     if(!(tn(r,'34193.1.5')===1 && tn(r,'34220.1.118')>0)) return null;
     const w = lastRows(H, 120), ratio = x=> tn(x,'34220.1.118')/simChargePmax(tn(x,'34183.1.9')/100);
     const rr = ratio(r);
     if(!(w.length>=12 && w.every(x=>tn(x,'34193.1.5')===1 && ratio(x)<0.85))) return [0, `Công suất sạc ${f1(tn(r,'34220.1.118'))} kW = ${Math.round(rr*100)}% đường sạc chuẩn — bình thường`];
     const precondSeen = H.some(x=>tn(x,'34233.4.4')===1);
     const cause = tn(r,'34220.1.80')>45 ? 'pin nóng, làm mát không kịp' : tn(r,'34220.1.78')<15 ? (precondSeen ? 'pin lạnh dù đã làm ấm (nghi PTC nước)' : 'pin lạnh, không được làm ấm trước') : 'chưa rõ';
     return [2, `Công suất sạc chỉ ${Math.round(rr*100)}% đường chuẩn ở SOC ${Math.round(tn(r,'34183.1.9'))}% trong 2 phút. Nguyên nhân: ${cause}`];
   }},
  {id:'d10', bai:'B10', name:'Sưởi kém / không sưởi', comp:'ptc_air', chart:'cc', faults:['ptc'],
   run(r, H){
     const w = lastRows(H, 600);
     if(w.length<60 || !w.every(x=>tv(x,'34184.1.5')==='heat')) return null;
     const d = tn(r,'34183.1.15') - tn(r,'34184.1.6');
     return d < -5 ? [2, `Sưởi hơn 10 phút mà cabin ${f1(tn(r,'34183.1.15'))}°C, thấp hơn cài đặt ${f1(-d)}°C${tn(r,'34233.2.198') ? ' · PTC báo lỗi (34233.2.198)' : ''}`]
                   : [0, `Cabin ${f1(tn(r,'34183.1.15'))}°C, gần nhiệt cài đặt — sưởi bình thường`];
   }},
  {id:'d8', bai:'B8', name:'Giảm công suất do nhiệt', comp:'motor', chart:'cm', truth:r=>r.plim,
   run(r){
     if(tn(r,'34183.1.10')!==1) return null;
     if(tn(r,'34200.1.68')){
       const tq = Math.abs(tn(r,'34233.3.148'))+Math.abs(tn(r,'34233.3.153'));
       const cause = tn(r,'34183.1.7')>38 ? 'nhiệt độ môi trường cao' : tq>250 ? 'tải nặng' : 'hệ làm mát kém';
       return [2, `Cờ giới hạn công suất (34200.1.68) bật — nguyên nhân: ${cause}`];
     }
     if(tn(r,'34233.3.232')>80 || tn(r,'34233.3.231')>110) return [1, `EDS ${f1(tn(r,'34233.3.232'))}°C / motor ${f1(tn(r,'34233.3.231'))}°C đang tiến gần ngưỡng giới hạn`];
     return [0, `EDS ${f1(tn(r,'34233.3.232'))}°C, motor ${f1(tn(r,'34233.3.231'))}°C — bình thường`];
   }},
  {id:'d12', bai:'B12', name:'Van chia nước kẹt', comp:'valve4', chart:'cm', faults:['valve'],
   run(r){ return tn(r,'34233.2.11')>0 ? [2, 'VCU báo lỗi van (34233.2.11). Không có vị trí van nên chỉ dựa được vào cờ lỗi']
                                        : [0, 'Không có cờ lỗi van. Telemetry không có vị trí van để kiểm tra kỹ hơn']; }},
  {id:'d13', bai:'B13', name:'Lọc gió cabin tắc', comp:'filter', chart:'cc', faults:['filter'], blind:true,
   run(r){ return tv(r,'34184.1.5')==='off' ? null : [0, 'Không kiểm tra được: telemetry không có công suất / tốc độ blower']; }}
];
let DET_ST = {};
function detReset(){ DET_ST = {}; DET.forEach(d=>{ DET_ST[d.id] = {status:0, ev:'Chưa đủ điều kiện để kiểm tra', first:null, firstEv:'', alarm:null, ex:false}; }); }
function detRun(r){
  r.det = {}; r.detEx = {}; r.truthD = {};
  DET.forEach(d=>{
    const st = DET_ST[d.id], out = d.run(r, simRows);
    if(out){ st.ex = true; st.status = out[0]; st.ev = out[1];
      if(out[0]>=1 && st.first===null){ st.first = r.t; st.firstEv = out[1]; }
      if(out[0]===2 && st.alarm===null){ st.alarm = r.t; st.firstEv = out[1]; } }
    r.det[d.id] = out ? out[0] : 0; r.detEx[d.id] = !!out;
    r.truthD[d.id] = d.truth ? !!d.truth(r) : d.faults.some(k=>r.fa.includes(k));
  });
}
function detEval(d){
  const st = DET_ST[d.id];
  const tr = simRows.find(x=>x.truthD && x.truthD[d.id]);
  if(d.blind) return tr ? ['fn', 'Bỏ sót — lỗi đang có nhưng telemetry thiếu tín hiệu để phát hiện'] : ['na', 'Không phát hiện được với telemetry hiện có'];
  if(!st.ex && !tr) return ['na', 'Kịch bản này chưa tạo điều kiện để kiểm tra'];
  if(tr && st.alarm!==null){
    const lag = st.alarm - tr.t;
    return lag >= 0 ? ['tp', `Đúng — phát hiện sau ${simFmtT(lag)} kể từ khi lỗi xuất hiện`] : ['tp', 'Đúng — phát hiện (cờ bật trước khi nhãn lỗi ghi nhận)'];
  }
  if(tr) return st.ex ? ['fn', 'Bỏ sót — có lỗi thật nhưng chưa phát hiện'] : ['na', 'Có lỗi nhưng kịch bản chưa tạo điều kiện để kiểm tra'];
  if(st.alarm!==null) return ['fp', 'Báo nhầm — không có lỗi thật cho bài này'];
  return ['tn', 'Đúng — không có lỗi, không báo'];
}
const DET_ST_TXT = {0:'Bình thường', 1:'Nghi ngờ', 2:'Phát hiện'};
const DET_EV_TXT = {tp:'Đúng', tn:'Đúng', fp:'Báo nhầm', fn:'Bỏ sót', na:'—'};
function detRender(){
  const host = $('#simDets'); if(!host) return;
  const ev = DET.map(d=>[d, detEval(d)]);
  const cnt = {tp:0, tn:0, fp:0, fn:0, na:0}; ev.forEach(([,e])=>cnt[e[0]]++);
  host.innerHTML = `<div class="det-sum"><b>Phát hiện lỗi</b> — chỉ đọc cột telemetry, so với lỗi đã bơm vào:
      <span class="ev ev-tp">Đúng ${cnt.tp+cnt.tn}</span><span class="ev ev-fp">Báo nhầm ${cnt.fp}</span><span class="ev ev-fn">Bỏ sót ${cnt.fn}</span><span class="ev ev-na">Chưa kiểm tra ${cnt.na}</span></div>
    <div class="det-grid">${ev.map(([d,e])=>{
      const st = DET_ST[d.id], s = !st.ex ? 'na' : st.status;
      const icon = s==='na' ? '–' : s===2 ? '!' : s===1 ? '?' : '✓';
      return `<div class="det det-${s}"><div class="det-h"><button type="button" class="det-name" data-id="${d.comp}">${d.name}</button><span>Bài ${d.bai}</span></div>
        <div class="det-st"><i aria-hidden="true">${icon}</i>${s==='na' ? 'Chưa đủ điều kiện' : DET_ST_TXT[s]}${st.first!==null ? ` · lần đầu lúc ${simFmtT(st.first)}` : ''}</div>
        <p>${st.first!==null && st.status<1 ? st.firstEv + ' <span class="note">(lần phát hiện đầu)</span>' : st.ev}</p>
        <div class="det-ev ev-${e[0]}">${DET_EV_TXT[e[0]]}${e[0]==='na' ? '' : ' · '}${e[0]==='na' ? e[1] : e[1].replace(/^(Đúng|Báo nhầm|Bỏ sót) — /,'')}</div></div>`;
    }).join('')}</div>`;
}

/* ---- bộ cột cố định: luôn xuất đủ 279 tín hiệu của thermal_hvac_signals.csv
   Mỗi tín hiệu: [cách sinh, hàm]. Cách sinh: 'vat_ly' (tính từ mô hình nhiệt / điện), 'suy_ra' (luật trên trạng thái
   mô phỏng: ngưỡng cảnh báo, bản trùng, cộng dồn, GPS), 'co_dinh' (cấu hình xe), 'trong' (không áp dụng / không có sự kiện).
   Mã hóa giá trị (1/0, chuỗi D/P, đơn vị) là giả định vì từ điển không ghi. */
const b01 = v => v ? 1 : 0;
const SIM_GEN = {
  // định danh / cấu hình
  '34180.1.1':['co_dinh', r=>r.vin], '34181.1.7':['co_dinh', ()=>'SIM-EV'], '34181.1.1':['co_dinh', ()=>({front:'FWD',rear:'RWD',dual:'AWD'})[drive]],
  '34181.1.2':['co_dinh', ()=>'SUV'], '34181.1.4':['co_dinh', ()=>'BEV'], '34181.1.5':['co_dinh', ()=>2026], '34181.1.6':['co_dinh', ()=>'VN'],
  '34220.1.110':['co_dinh', ()=>'NMC'], '34220.1.82':['co_dinh', ()=>60], '34220.1.111':['co_dinh', ()=>'SIM-BAT-0001'],
  '34220.1.113':['co_dinh', ()=>'2025-11-01'], '34184.1.1':['co_dinh', ()=>'SIM-HVAC-01'], '34184.1.2':['co_dinh', ()=>'SIM'],
  '34184.1.3':['co_dinh', ()=>'SIM-1.0'], '34183.1.6':['suy_ra', r=>r.ts], '34183.1.24':['co_dinh', ()=>'+07:00'],
  // trạng thái xe
  '34183.1.10':['suy_ra', r=>b01(r.phase==='drive')], '34193.1.35':['suy_ra', r=>b01(r.phase!=='park')],
  '34183.1.1':['suy_ra', r=>r.phase==='drive' ? 'D' : 'P'], '34183.1.32':['co_dinh', ()=>'Normal'],
  '34233.2.202':['suy_ra', r=>r.plim||r.hot||r.lowCool ? 2 : (r.fanErr||r.ptcErr||r.cold) ? 1 : 0],
  '34233.2.203':['suy_ra', r=>({drive:1, charge:2, park:0})[r.phase]],
  '34183.1.30':['vat_ly', r=>r.park], '34183.1.2':['vat_ly', r=>r.v], '34183.1.3':['vat_ly', r=>r.odo],
  '34183.1.9':['vat_ly', r=>r.soc], '34220.1.2':['vat_ly', r=>r.soc+0.4], '34183.1.26':['vat_ly', r=>r.pedal],
  '34183.1.31':['suy_ra', r=>r.phase==='drive' ? 2 : r.phase==='charge' && SIM_SCN[r.scn].acWhileCharging ? 1 : 0],
  // môi trường & vị trí
  '34183.1.7':['vat_ly', r=>r.Ta], '34233.4.21':['suy_ra', ()=>0],
  '6.1.0':['vat_ly', r=>r.lat], '6.1.1':['vat_ly', r=>r.lon], '6.1.2':['vat_ly', r=>r.alt],
  // HVAC cabin
  '34183.1.15':['vat_ly', r=>r.Tcab], '34184.1.42':['suy_ra', r=>b01(r.mode!=='off')], '34184.1.5':['suy_ra', r=>r.mode],
  '34184.1.32':['suy_ra', r=>r.mode], '34184.1.10':['suy_ra', r=>b01(r.mode==='cool' && r.Tcab-r.set>6)],
  '34184.1.11':['suy_ra', r=>b01(r.recirc)], '34184.1.9':['suy_ra', r=>b01(r.mode==='heat' && r.Ta<12 && r.phase==='drive' && r.t<300)],
  '34184.1.27':['suy_ra', r=>b01(r.rearDefrost)], '34184.1.23':['co_dinh', ()=>1], '34184.1.4':['suy_ra', r=>b01(r.mode!=='off')],
  '34184.1.41':['suy_ra', r=>r.blower], '34184.1.6':['suy_ra', r=>r.set], '34184.1.7':['suy_ra', r=>r.set],
  '34184.1.25':['suy_ra', r=>r.blower], '34184.1.24':['suy_ra', r=>r.blower],
  '34184.1.12':['suy_ra', r=>r.mode==='heat' ? 'foot' : r.mode==='cool' ? 'face' : 'off'], '34184.1.26':['suy_ra', r=>r.mode==='heat' ? 'foot' : r.mode==='cool' ? 'face' : 'off'],
  '34184.1.28':['suy_ra', r=>r.mode==='heat' ? 2 : 0], '34184.1.29':['suy_ra', r=>r.mode==='heat' && r.phase==='drive' ? 1 : 0],
  '34184.1.33':['suy_ra', ()=>0], '34184.1.34':['suy_ra', ()=>0],
  '34184.1.30':['suy_ra', r=>r.mode==='cool' && r.Tcab>28 ? 2 : 0], '34184.1.31':['suy_ra', ()=>0],
  '34184.1.35':['suy_ra', ()=>0], '34184.1.36':['suy_ra', ()=>0],
  '34184.1.37':['suy_ra', ()=>0], '34184.1.38':['suy_ra', ()=>0], '34184.1.39':['suy_ra', ()=>0], '34184.1.40':['suy_ra', ()=>0],
  '34199.1.15':['suy_ra', ()=>0], '34199.1.17':['suy_ra', ()=>0],
  '34233.2.13':['suy_ra', r=>r.gas<50 ? 1 : 0], '34200.11.2':['suy_ra', r=>b01(r.gas<50 || r.ptcErr)], '34200.1.24':['suy_ra', ()=>0],
  '34233.2.156':['suy_ra', r=>b01(r.phase!=='park')], '34233.2.176':['suy_ra', r=>b01(drive==='dual' && r.phase!=='park')],
  // lệnh từ app / lịch điều hòa: chỉ có giá trị khi có lệnh → để trống
  '34199.1.1':['trong', ()=>''], '34199.1.2':['trong', ()=>''], '34199.1.3':['trong', ()=>''], '34199.1.4':['trong', ()=>''],
  '34199.1.5':['trong', ()=>''], '34199.1.7':['trong', ()=>''], '34199.1.8':['trong', ()=>''], '34199.1.9':['trong', ()=>''],
  '34199.1.10':['trong', ()=>''], '34199.1.11':['trong', ()=>''], '34199.1.12':['trong', ()=>''], '34199.1.13':['trong', ()=>''],
  '34199.1.14':['trong', ()=>''],
  '34224.1.2':['co_dinh', ()=>0], '34224.1.3':['trong', ()=>''], '34224.1.11':['co_dinh', ()=>0],
  '34224.1.4':['co_dinh', ()=>3], '34224.1.5':['co_dinh', r=>r.set], '34224.1.6':['co_dinh', r=>r.set],
  // vòng gas lạnh
  '34233.9.39':['vat_ly', r=>r.Tev], '34233.2.184':['suy_ra', r=>b01(r.gas<45)], '34233.2.183':['suy_ra', ()=>0],
  '34233.2.199':['suy_ra', ()=>0], '34233.2.9':['suy_ra', r=>r.fanErr], '34233.2.6':['suy_ra', ()=>0], '34200.2.32':['suy_ra', ()=>0],
  // vòng nước pin & nhiệt pin
  '34220.1.104':['vat_ly', r=>r.TcIn], '34220.1.105':['vat_ly', r=>r.TcOut], '34220.1.109':['vat_ly', r=>r.coolReq],
  '34220.1.80':['vat_ly', r=>r.Tmax], '34220.1.78':['vat_ly', r=>r.Tmin], '34220.1.81':['vat_ly', r=>r.Tmax-r.Tmin],
  '34220.1.77':['suy_ra', r=>r.phase==='charge' ? 17 : 23], '34220.1.79':['suy_ra', ()=>4],
  '34233.4.10':['vat_ly', r=>r.Tmax], '34233.4.11':['vat_ly', r=>r.Tmin], '34233.4.12':['vat_ly', r=>r.Tmax-r.Tmin],
  '34233.4.13':['suy_ra', r=>r.phase==='charge' ? 17 : 23], '34233.4.14':['suy_ra', ()=>4],
  '34220.1.3':['vat_ly', r=>r.Tpack], '34220.1.83':['vat_ly', r=>r.Tpack], '34233.4.15':['vat_ly', r=>r.Tpack],
  '34233.4.2':['vat_ly', r=>r.Tbdu],
  '34233.8.12':['suy_ra', r=>b01(r.pumpB)], '34233.9.22':['suy_ra', r=>b01(r.pumpB)],
  '34233.2.16':['suy_ra', r=>b01(r.pumpFault!==null && r.pumpFault<50)], '34233.2.192':['suy_ra', r=>b01(r.pumpFault!==null && r.pumpFault<=20)],
  '34233.4.4':['suy_ra', r=>b01(r.precond)], '34233.2.10':['suy_ra', r=>r.ptcErr ? 2 : 0], '34233.2.198':['suy_ra', r=>b01(r.ptcErr)],
  '34220.1.93':['suy_ra', r=>b01(r.cold)], '34220.1.97':['suy_ra', ()=>0], '34200.6.14':['suy_ra', ()=>0],
  '34200.1.76':['suy_ra', ()=>0], '34200.25.20':['suy_ra', ()=>0], '34200.7.1':['suy_ra', r=>b01(r.lowCool)],
  '34220.1.90':['suy_ra', r=>b01(r.Tmax>48)], '34220.1.99':['suy_ra', r=>b01(r.Tmax-r.Tmin>8)], '34220.1.100':['suy_ra', r=>b01(r.Tbdu>70)],
  '34220.1.15':['suy_ra', r=>b01(r.Tmax-r.Tmin>10)], '34220.1.16':['suy_ra', r=>b01(r.Tmax>55)], '34220.1.17':['suy_ra', r=>b01(r.Tmin<-10)],
  '34233.2.242':['suy_ra', r=>b01(r.Tmax>55)], '34233.2.243':['suy_ra', r=>b01(r.Tmax-r.Tmin>10)], '34233.2.245':['suy_ra', r=>b01(r.Tmin<-10)],
  '34220.1.42':['suy_ra', ()=>0], '34220.1.44':['suy_ra', ()=>0], '34220.1.45':['suy_ra', ()=>0],
  '34200.1.31':['suy_ra', r=>b01(r.hot)], '34200.25.13':['suy_ra', r=>b01(r.hot)],
  '34200.6.6':['suy_ra', r=>b01(r.Tmax>50)], '34200.6.7':['suy_ra', r=>b01(r.Tmax>55)],
  '34200.1.71':['suy_ra', r=>b01(r.Tmin<5)], '34200.25.14':['suy_ra', r=>b01(r.Tmin<5)],
  '34200.6.5':['suy_ra', r=>b01(r.Tmin<0)], '34200.2.27':['suy_ra', r=>b01(r.Tmin<-20)],
  '34200.6.11':['suy_ra', r=>b01(r.Tbdu>70)], '34200.6.12':['suy_ra', r=>b01(r.Tbdu>80)], '34200.6.13':['suy_ra', r=>b01(r.Tbdu>95)],
  '34220.1.91':['suy_ra', ()=>0], '34220.1.116':['suy_ra', ()=>0], '34220.1.18':['suy_ra', ()=>0],
  '34200.1.72':['suy_ra', ()=>0], '34200.25.15':['suy_ra', ()=>0], '34200.6.4':['suy_ra', ()=>0],
  // pin: điện & giới hạn
  '34220.1.59':['vat_ly', r=>r.I], '34233.4.16':['vat_ly', r=>r.I], '34220.1.60':['vat_ly', r=>r.Vp],
  '34220.1.106':['vat_ly', r=>r.Iallow], '34220.1.107':['vat_ly', r=>r.Idis*1.5], '34233.4.17':['vat_ly', r=>r.Idis], '34233.4.18':['vat_ly', r=>r.Idis*1.5],
  '34220.1.75':['suy_ra', r=>r.phase==='charge' && r.Pch>0 ? 460 : 0], '34220.1.76':['vat_ly', r=>r.phase==='charge' && r.Pch>0 ? r.Iallow : 0],
  '34220.1.70':['suy_ra', r=>b01(r.Tmax>55 || r.Tmin<-10)], '34233.1.17':['suy_ra', r=>b01(r.Tmax>55 || r.Tmin<-10)], '34233.9.9':['suy_ra', r=>b01(r.Tmax>55 || r.Tmin<-10)],
  '34220.1.1':['co_dinh', ()=>96.5],
  // sạc
  '34220.1.118':['vat_ly', r=>r.Pch], '34220.1.117':['vat_ly', r=>r.Pch/60],
  '34193.1.5':['suy_ra', r=>b01(r.phase==='charge' && r.Pch>0)], '34193.1.32':['suy_ra', r=>r.phase==='charge' ? 'DC' : ''],
  '34193.1.17':['suy_ra', r=>b01(r.phase==='charge')], '34193.1.1':['suy_ra', ()=>0], '34193.1.31':['suy_ra', r=>b01(r.phase==='charge')],
  '34193.1.30':['suy_ra', r=>b01(r.fastLong)], '34193.1.28':['suy_ra', ()=>0],
  '34193.1.19':['co_dinh', ()=>80], '34193.1.7':['vat_ly', r=>r.chgLeft], '34220.1.74':['vat_ly', r=>r.chgLeft],
  '34233.9.34':['suy_ra', ()=>0], '34233.9.36':['vat_ly', r=>r.phase==='charge' ? r.Vp : 0], '34233.9.38':['suy_ra', r=>b01(r.phase==='charge' && r.Pch>0)],
  '34200.1.29':['suy_ra', ()=>0], '34200.1.239':['suy_ra', r=>b01(r.phase==='charge' && r.soc>=79.9)], '34200.1.240':['suy_ra', r=>b01(r.phase==='charge' && r.Pch>0)],
  // vòng nước motor & điện tử công suất
  '34233.8.11':['suy_ra', r=>b01(r.pumpM)], '34233.9.17':['suy_ra', r=>b01(r.pumpM)],
  '34233.3.231':['vat_ly', r=>r.Tm], '34233.3.232':['vat_ly', r=>r.Tinv],
  '34233.3.148':['vat_ly', r=>r.tqF], '34233.3.153':['vat_ly', r=>r.tqR],
  '34233.3.147':['suy_ra', r=>b01(r.phase==='drive' && drive!=='rear')], '34233.3.152':['suy_ra', r=>b01(r.phase==='drive' && drive!=='front')],
  '34233.3.155':['vat_ly', r=>drive!=='rear' ? r.rpm : 0], '34233.3.157':['vat_ly', r=>drive!=='front' ? r.rpm : 0],
  '34233.3.146':['suy_ra', r=>b01(r.phase==='drive' && drive!=='rear')], '34233.3.151':['suy_ra', r=>b01(r.phase==='drive' && drive!=='front')],
  '34233.3.10':['suy_ra', r=>b01(r.Tcm>75 && drive!=='rear')], '34233.3.34':['suy_ra', r=>b01(r.Tcm>75 && drive!=='front')],
  '34233.3.3':['suy_ra', r=>b01(r.Tm>120)], '34233.3.4':['suy_ra', r=>b01(r.Tm>140)],
  '34233.3.27':['suy_ra', r=>b01(drive!=='front' && r.Tm>120)], '34233.3.28':['suy_ra', r=>b01(drive!=='front' && r.Tm>140)],
  '34233.3.9':['suy_ra', r=>b01(r.Tinv>80)], '34233.3.33':['suy_ra', r=>b01(drive!=='front' && r.Tinv>80)],
  '34233.3.6':['suy_ra', r=>b01(r.Tinv>95)], '34233.3.7':['suy_ra', r=>b01(r.Tinv>95)], '34233.3.8':['suy_ra', r=>b01(r.Tinv>95)],
  '34233.3.30':['suy_ra', r=>b01(drive!=='front' && r.Tinv>95)], '34233.3.31':['suy_ra', r=>b01(drive!=='front' && r.Tinv>95)], '34233.3.32':['suy_ra', r=>b01(drive!=='front' && r.Tinv>95)],
  '34233.3.57':['suy_ra', r=>b01(r.Tinv>95)], '34233.3.58':['suy_ra', r=>b01(r.Tinv>85)],
  '34233.3.88':['suy_ra', r=>b01(drive!=='front' && r.Tinv>95)], '34233.3.89':['suy_ra', r=>b01(drive!=='front' && r.Tinv>85)],
  '34233.3.56':['suy_ra', r=>b01(r.Tinv>85)], '34233.3.87':['suy_ra', r=>b01(drive!=='front' && r.Tinv>85)],
  '34233.3.66':['suy_ra', ()=>0], '34233.3.97':['suy_ra', ()=>0],
  '34233.3.52':['suy_ra', r=>b01(r.plim)], '34233.3.83':['suy_ra', r=>b01(drive!=='front' && r.plim)],
  '34233.3.5':['suy_ra', ()=>0], '34233.3.29':['suy_ra', ()=>0], '34233.3.11':['suy_ra', ()=>0], '34233.3.35':['suy_ra', ()=>0],
  '34233.3.169':['suy_ra', ()=>0], '34233.3.170':['suy_ra', ()=>0], '34233.3.204':['suy_ra', ()=>0], '34233.3.205':['suy_ra', ()=>0],
  '34233.6.23':['suy_ra', ()=>0], '34233.6.24':['suy_ra', ()=>0], '34233.6.75':['suy_ra', ()=>0], '34233.6.76':['suy_ra', ()=>0],
  '34233.3.1':['suy_ra', ()=>0], '34233.3.2':['suy_ra', r=>r.plim ? 2 : 0], '34233.3.25':['suy_ra', ()=>0],
  '34233.3.26':['suy_ra', r=>drive!=='front' && r.plim ? 2 : 0], '34233.2.8':['suy_ra', r=>r.plim ? 1 : 0],
  '34233.2.18':['suy_ra', ()=>0], '34233.2.213':['suy_ra', ()=>0], '34233.2.215':['suy_ra', ()=>0], '34233.2.210':['suy_ra', ()=>0],
  '34233.2.229':['suy_ra', ()=>0], '34233.2.226':['co_dinh', ()=>11],
  '34233.2.19':['suy_ra', ()=>0], '34233.9.25':['suy_ra', ()=>0],
  '34233.9.35':['vat_ly', r=>r.Idcdc], '34233.9.37':['vat_ly', r=>r.phase==='park' ? 12.6 : 13.8],
  '34233.2.11':['suy_ra', r=>r.valveFault ? 2 : 0], '34233.2.12':['suy_ra', ()=>0],
  '34200.11.1':['suy_ra', r=>b01(r.lowCool || r.valveFault || (r.pumpFault!==null && r.pumpFault<30))],
  '34200.1.68':['suy_ra', r=>b01(r.plim)], '34200.25.28':['suy_ra', r=>b01(r.plim)],
  '34200.9.5':['suy_ra', r=>b01(r.plim)], '34200.9.6':['suy_ra', r=>b01(r.plim)],
  // năng lượng & chuyến
  '34198.1.6':['vat_ly', r=>r.eClim], '34198.1.7':['vat_ly', r=>r.eMot], '34198.1.8':['vat_ly', r=>r.eDcdc],
  '34198.1.4':['vat_ly', r=>r.eTot], '34198.1.5':['vat_ly', r=>r.dist>0.5 ? r.eTot/r.dist*100 : 0], '34198.1.3':['vat_ly', r=>r.dist],
  '34198.1.1':['suy_ra', r=>r.ts0], '34198.1.2':['suy_ra', r=>r.ts],
  '34187.1.2':['vat_ly', r=>r.dist], '34187.1.3':['vat_ly', r=>r.driveT>0 ? r.dist/(r.driveT/3600) : 0], '34187.1.5':['vat_ly', r=>r.dist>0.5 ? r.eTot/r.dist*100 : 0],
  '34187.2.2':['vat_ly', r=>r.dist+142.6], '34187.2.3':['co_dinh', ()=>38.5], '34187.2.5':['co_dinh', ()=>17.8],
  '34187.3.2':['vat_ly', r=>r.odo-0.3], '34187.3.3':['co_dinh', ()=>41.2], '34187.3.5':['co_dinh', ()=>18.4],
  '34187.1.6':['trong', ()=>''], '34187.2.6':['trong', ()=>''], '34187.3.6':['trong', ()=>''],
  // DTC: chỉ có khi ECU ghi lỗi; mã DTC thật chưa có bảng → để trống
  '34201.1.2':['trong', ()=>''], '34201.1.1':['trong', ()=>''], '34200.1.253':['suy_ra', ()=>0]
};
const SIM_UNITS = {'34183.1.2':'km/h','34183.1.3':'km','34183.1.9':'%','34220.1.2':'%','34183.1.30':'min','34183.1.7':'°C','34183.1.15':'°C',
  '34233.9.39':'°C','34220.1.104':'°C','34220.1.105':'°C','34220.1.80':'°C','34220.1.78':'°C','34220.1.81':'°C','34233.4.10':'°C','34233.4.11':'°C',
  '34233.4.12':'°C','34220.1.3':'°C','34220.1.83':'°C','34233.4.15':'°C','34233.4.2':'°C','34233.3.231':'°C','34233.3.232':'°C','34220.1.109':'kW',
  '34220.1.59':'A','34233.4.16':'A','34220.1.60':'V','34220.1.106':'A','34220.1.107':'A','34233.4.17':'A','34233.4.18':'A','34220.1.75':'V','34220.1.76':'A',
  '34220.1.118':'kW','34233.3.148':'Nm','34233.3.153':'Nm','34233.3.155':'rpm','34233.3.157':'rpm','34233.9.35':'A','34233.9.37':'V',
  '34198.1.6':'kWh','34198.1.7':'kWh','34198.1.8':'kWh','34198.1.4':'kWh','34198.1.5':'kWh/100km','34198.1.3':'km','34187.1.2':'km','34187.2.2':'km',
  '34187.3.2':'km','34187.1.3':'km/h','34187.1.5':'kWh/100km','34183.1.26':'%','6.1.2':'m','34193.1.7':'min','34220.1.74':'min','34184.1.6':'°C','34184.1.7':'°C'};
const SIM_TRUTH = [
  ['_ctx_scenario', r=>r.scn], ['_ctx_phase', r=>r.phase], ['_ctx_drive_config', ()=>drive],
  ['_truth_faults', r=>r.faults], ['_truth_compressor_speed [0-1]', r=>r.comp], ['_truth_compressor_power [kW]', r=>r.Pcomp],
  ['_truth_fan_cmd [0-1]', r=>r.fanCmd], ['_truth_fan_actual [0-1]', r=>r.fanAct], ['_truth_chiller_valve [1/0]', r=>b01(r.chillerOpen)],
  ['_truth_chiller_heat [kW]', r=>r.Qch/1000], ['_truth_ptc_air_power [kW]', r=>r.PptcAir/1000], ['_truth_ptc_water_power [kW]', r=>r.PptcW/1000],
  ['_truth_batt_coolant_flow [0-1]', r=>r.flowB], ['_truth_refrigerant_charge [%]', r=>r.gas], ['_truth_coolant_level [%]', r=>r.level*100],
  ['_truth_motor_coolant_temp [°C]', r=>r.Tcm], ['_truth_coolant_inlet_true [°C]', r=>r.TcInTrue], ['_truth_valve_serial [1/0]', r=>b01(r.serial)],
  ['_truth_vent_outlet_temp [°C]', r=>r.Tvent]
];
function simColumns(){
  const cols = SIGNALS.map(s=>{
    const g = SIM_GEN[s[0]];
    const u = SIM_UNITS[s[0]];
    return [`content.${s[0]} ${s[1]}${u ? ' ['+u+']' : ''}`, g ? g[1] : ()=>''];
  });
  return cols.concat(SIM_TRUTH, DET.map(d=>[`_det_${d.bai.replace(/ · /g,'_')} ${d.name} [0 bình thường / 1 nghi ngờ / 2 phát hiện]`, r=>r.det ? r.det[d.id] : 0]));
}

/* ================================================================== SIMULATION
   Mô hình nhiệt gộp bậc 1 (lumped) + bộ điều khiển kiểu CCU / BMS / VCU.
   Đủ để ra xu hướng giống thật (sạc nhanh nóng pin, rò gas làm dàn lạnh ấm lên, quạt chết làm
   điều hòa yếu khi xe đứng…), KHÔNG phải mô hình đã hiệu chuẩn theo xe VinFast. */
const SIM_PH = {drive:'Lái xe', charge:'Sạc nhanh DC', park:'Đỗ xe'};
const SIM_SCN = {
  hcm:{label:'Trưa nắng TP.HCM 35°C: lái 35 phút → sạc nhanh DC', start:'2026-04-15T11:30:00+07:00', speed:60,
    loc:[10.7769,106.7009,5], amb:t=>35+1.5*Math.sin(t/7200*Math.PI), solar:()=>800, setpoint:22, soc:0.42, acWhileCharging:true,
    init:{cab:52, b:38, cb:37, m:40, cm:38},
    phases:[{type:'drive', dur:35*60, cycle:'mixed'},{type:'charge', dur:35*60},{type:'park', dur:15*60}]},
  hn:{label:'Sáng đông Hà Nội 10°C: lái 30 phút (làm ấm pin) → sạc nhanh', start:'2026-01-10T07:00:00+07:00', speed:60,
    loc:[21.0285,105.8542,15], amb:t=>10+t/3600*1.5, solar:()=>120, setpoint:24, soc:0.35, acWhileCharging:true, precondFrom:15*60,
    init:{cab:10, b:10, cb:10, m:10, cm:10},
    phases:[{type:'drive', dur:30*60, cycle:'mixed'},{type:'charge', dur:35*60},{type:'park', dur:15*60}]},
  night:{label:'Đỗ qua đêm (cold soak) 11 giờ → sáng lái 20 phút', start:'2026-06-01T18:00:00+07:00', speed:1200, loc:[10.8505,106.7719,10],
    amb:t=>{ const h=(18+t/3600)%24; return 27+3.5*Math.cos((h-15)/24*2*Math.PI); },
    solar:t=>{ const h=(18+t/3600)%24; return h>6 && h<18 ? 600*Math.sin((h-6)/12*Math.PI) : 0; },
    setpoint:23, soc:0.6, init:{cab:38, b:37, cb:36, m:65, cm:55},
    phases:[{type:'park', dur:11*3600},{type:'drive', dur:20*60, cycle:'city'}]},
  pass:{label:'Leo đèo nắng nóng 38°C: cao tốc → dốc 8% → phố', start:'2026-05-20T13:00:00+07:00', speed:60,
    loc:[16.1900,108.1300,50], amb:()=>38, solar:()=>900, setpoint:22, soc:0.85, init:{cab:40, b:33, cb:32, m:38, cm:37},
    phases:[{type:'drive', dur:15*60, cycle:'highway'},{type:'drive', dur:20*60, cycle:'climb'},{type:'drive', dur:10*60, cycle:'city'},{type:'park', dur:10*60}]}
};
const SIM_FAULTS = [
  {id:'gas',    label:'Rò gas lạnh — lượng gas còn lại', min:40, max:100, def:60, unit:'%', probs:'3, 4, B7'},
  {id:'pump',   label:'Bơm nước pin suy giảm — lưu lượng còn lại', min:10, max:100, def:40, unit:'%', probs:'1, B6'},
  {id:'fan',    label:'Quạt két chết', bool:true, probs:'4, B8, B9'},
  {id:'chiller',label:'Chiller kém — hiệu suất còn lại', min:10, max:100, def:15, unit:'%', probs:'4, B6, B9'},
  {id:'leak',   label:'Rò nước làm mát — tốc độ rò', min:5, max:100, def:40, unit:'%/giờ', probs:'1, B6, B8'},
  {id:'offset', label:'Cảm biến nước vào pin lệch', min:-10, max:10, def:6, unit:'°C', probs:'B5'},
  {id:'ptc',    label:'PTC hỏng (gió và nước)', bool:true, probs:'B9, B10'},
  {id:'filter', label:'Lọc gió cabin tắc', min:10, max:90, def:60, unit:'%', probs:'B13'},
  {id:'valve',  label:'Van 4 ngả kẹt ở chế độ nối vòng', bool:true, probs:'B12'}
];
// [key, nhãn, slot màu]; ref = đường tham chiếu nét đứt màu trung tính
const SIM_CHARTS = [
  {id:'cb', title:'Pin', unit:'°C', s:[['Tmax','Nhiệt cell lớn nhất',1],['TcIn','Nước vào pin',2],['TcOut','Nước ra pin',3]]},
  {id:'cc', title:'Cabin & dàn lạnh', unit:'°C', s:[['Tcab','Nhiệt cabin',1],['Tev','Nhiệt dàn lạnh',2],['set','Nhiệt cài đặt',3]], ref:['Ta','Ngoài trời']},
  {id:'cm', title:'Motor & EDS', unit:'°C', s:[['Tm','Nhiệt motor',1],['Tinv','Nhiệt EDS',2]], ref:['Ta','Ngoài trời']},
  {id:'cp', title:'Công suất', unit:'kW', s:[['Pch','Sạc',1],['coolReq','BMS yêu cầu làm mát',2],['Pcomp','Máy nén (không có trong telemetry)',3]]}
];
let simOn=false, simRunning=false, simScnKey='hcm', simSpeed=60, SIM=null, simRows=[], simNext=0, simAcc=0, simDrawT=0;
let SIM_F = {}, SIM_FON = {};
const simBase = ()=> Date.parse(SIM_SCN[simScnKey].start);
const simDuration = sc => sc.phases.reduce((a,p)=>a+p.dur, 0);
const clamp = (v,a,b)=> Math.max(a, Math.min(b, v));

function simPhaseAt(sc, t){
  let acc = 0;
  for(const p of sc.phases){ if(t < acc+p.dur) return {type:p.type, cycle:p.cycle, since:t-acc}; acc += p.dur; }
  const p = sc.phases[sc.phases.length-1]; return {type:p.type, cycle:p.cycle, since:p.dur};
}
function simCityV(s){ const c = s%150; return c<20 ? c/20*45 : c<110 ? 45+5*Math.sin(c/9) : c<125 ? (125-c)/15*45 : 0; }
function simSpeedOf(cycle, s){
  if(cycle==='highway') return Math.min(100, s*1.5)*(1+0.04*Math.sin(s/90));
  if(cycle==='climb') return 70+6*Math.sin(s/70);
  if(cycle==='mixed') return Math.floor(s/600)%2===0 ? simCityV(s) : 70+5*Math.sin(s/50);
  return simCityV(s);
}
function simChargePmax(soc){ return soc<0.5 ? 120 : soc<0.8 ? 120-(soc-0.5)/0.3*70 : Math.max(15, 50-(soc-0.8)/0.15*35); }
function simThermalF(Tmax, Tmin){
  let f = 1;
  if(Tmax>45) f = Math.max(0.25, 1-(Tmax-45)/8*0.75);
  if(Tmin<20) f = Math.min(f, Math.max(0.15, 0.15+0.85*Tmin/20));
  return f;
}

function simReadFaults(){
  SIM_FAULTS.forEach(f=>{
    const on = $('#f_'+f.id).checked;
    const val = f.bool ? true : +$('#fv_'+f.id).value;
    if(!f.bool) $('#fvt_'+f.id).textContent = `${val} ${f.unit}`;
    if(on && !SIM_F[f.id] && SIM) SIM_FON[f.id] = SIM.t;
    SIM_F[f.id] = on ? val : null;
  });
}
function simFaultLabel(){
  return Object.entries(SIM_F).filter(([,v])=>v!==null && v!==undefined && v!==false)
    .map(([k,v])=>`${k}${v===true?'':'='+v}@${Math.round((SIM_FON[k]||0)/60)}min`).join(';');
}

function simReset(){
  const sc = SIM_SCN[simScnKey], i = sc.init;
  SIM = {t:0, Tcab:i.cab, Tb:i.b, Tcb:i.cb, Tm:i.m, Tinv:i.m, Tcm:i.cm, Tev:i.cab, spread:1, soc:sc.soc, odo:18240,
         level:1, comp:0, vPrev:0, park:0, fastLongT:0, eClim:0, fanErr:0, ptcErr:false, view:null,
         Tbdu:i.b, eMot:0, eDcdc:0, eTot:0, dist:0, driveT:0, lat:sc.loc[0], lon:sc.loc[1], alt:sc.loc[2], head:0.6};
  SIM_FON = {}; Object.keys(SIM_F).forEach(k=>{ if(SIM_F[k]!==null) SIM_FON[k]=0; });
  simRows = []; simNext = 0; simAcc = 0; detReset();
  simStep(0); simSample(); simNext = 10;
  simDraw(); simClock();
}

function simStep(dt){
  const sc = SIM_SCN[simScnKey], F = SIM_F, S = SIM;
  const ph = simPhaseAt(sc, S.t);
  const Ta = sc.amb(S.t), sol = sc.solar(S.t);
  const driving = ph.type==='drive', charging = ph.type==='charge', parked = ph.type==='park';
  S.park = parked ? S.park+dt : 0;

  // ---- xe: tốc độ & công suất kéo
  const v = driving ? simSpeedOf(ph.cycle, ph.since) : 0, vm = v/3.6;
  const grade = driving && ph.cycle==='climb' ? 0.08 : 0;
  const acc = dt>0 ? clamp((vm-S.vPrev)/dt, -3, 3) : 0; S.vPrev = vm;
  const Pw = 2100*9.81*(0.011+grade)*vm + 0.5*1.2*0.72*vm*vm*vm + 2100*acc*vm;
  let Pdrive = !driving ? 0 : Pw>0 ? Pw/0.9 : Pw*0.6;
  const derate = S.Tm>130 || S.Tinv>90 || (S.Tb+S.spread/2)>52;
  if(derate && Pdrive>0) Pdrive *= 0.5;

  // ---- CCU: điều hòa cabin
  const occupied = driving || (charging && sc.acWhileCharging);
  const set = sc.setpoint;
  const mode = !occupied ? 'off' : Ta>=18 ? 'cool' : 'heat';
  const err = S.Tcab - set;
  const blower = mode==='off' ? 0 : clamp(Math.round(2+Math.abs(err)/2.5), 2, 7);
  const filt = F.filter ? 1-0.6*F.filter/100 : 1;
  const air = blower/7*filt;
  const recirc = mode==='cool' && err>3;
  const TinAir = recirc ? S.Tcab : 0.7*S.Tcab+0.3*Ta;

  // ---- BMS: nhu cầu làm mát / làm ấm pin
  const Tmax = S.Tb+S.spread/2, Tmin = S.Tb-S.spread/2;
  const coolReq = clamp((Tmax-(charging?32:38))*1.2, 0, 6);
  const precond = !!(sc.precondFrom && driving && S.t>=sc.precondFrom);
  const heatReq = Tmin<((charging||precond)?18:5) && Ta<20;

  // ---- VCU: van, bơm, quạt
  const serial = !!F.valve || (heatReq && driving && S.Tcm>S.Tcb+5);
  const levelF = S.level<0.6 ? Math.max(0.05, (S.level-0.2)/0.4) : 1;   // air enters the loop below ~60 %
  const pumpB = driving || charging || coolReq>0 || heatReq;
  const pumpM = driving || charging || S.Tcm>45;
  const flowB = pumpB ? (F.pump ? F.pump/100 : 1)*levelF : 0;
  const flowM = pumpM ? levelF : 0;
  let fanCmd = clamp((S.Tcm-42)/15, 0, 1);
  if(S.comp>0.05) fanCmd = Math.max(fanCmd, Ta>30 ? 0.6 : 0.35);
  if(v<5 && S.comp>0.3) fanCmd = Math.max(fanCmd, 0.8);
  const fanAct = F.fan ? 0 : fanCmd;
  if(F.fan && fanCmd>0.3) S.fanErr = 2;

  // ---- vòng gas lạnh
  const gas = F.gas ?? 100;
  const gasF = Math.pow(clamp((gas/100-0.45)/0.45, 0, 1), 0.7);
  const airCond = Math.min(1, vm/22+0.9*fanAct);
  const condF = 0.3+0.7*airCond;
  const QrefMax = 6500*gasF*condF*clamp(1-(Ta-35)*0.02, 0.6, 1.1);
  const chillerOpen = coolReq>0;
  const cabinCool = mode==='cool';
  let target = 0;
  // cabin share fades out once the cabin reaches the setpoint (otherwise the A/C over-cools)
  if(cabinCool) target += clamp((err+1)/2, 0, 1)*clamp(0.3+(S.Tev-3)*0.08, 0, 1);
  if(chillerOpen) target += Math.min(0.7, coolReq/6*0.9+0.2);
  target = Math.min(1, target);
  S.comp += (target-S.comp)*Math.min(1, dt/(target>S.comp ? 20 : 8));
  const Qref = S.comp*QrefMax;
  const chEff = F.chiller ? F.chiller/100 : 1;
  const QchReq = chillerOpen ? chEff*260*Math.max(0, S.Tcb-4)*Math.min(1, flowB+0.1) : 0;
  const Qch = Math.min(QchReq, cabinCool ? Qref*0.55 : Qref);
  const QrefEv = cabinCool ? Qref-Qch : 0;
  const QairEv = cabinCool ? 230*air*(TinAir-S.Tev) : 0;
  if(cabinCool) S.Tev += (QairEv-QrefEv)/3000*dt; else S.Tev += (TinAir-S.Tev)*Math.min(1, dt/120);
  S.Tev = Math.max(-3, S.Tev);

  // ---- sưởi PTC
  const ptcOK = !F.ptc;
  const PptcAir = mode==='heat' && ptcOK ? clamp((set+4-S.Tcab)*700, 0, 5000) : 0;
  const PptcW = heatReq && ptcOK ? 5000*clamp((45-S.Tcb)/10, 0, 1) : 0;
  if(F.ptc && (mode==='heat' || heatReq)) S.ptcErr = true;
  const Pcomp = Qref/(2.8*condF+0.2);
  const Pblower = mode==='off' ? 0 : (30+220*Math.pow(blower/7, 2))*(1+0.4*(F.filter||0)/100);

  // ---- cabin
  const Qcab = 130*(Ta-S.Tcab) + sol*0.7 + (occupied?120:0) + PptcAir*0.95 - QairEv;
  S.Tcab += Qcab/90000*dt;

  // ---- pin: điện
  const Vp = 330+70*S.soc;
  const fT = simThermalF(Tmax, Tmin);
  let Pch = 0;
  if(charging && S.soc<0.8) Pch = simChargePmax(S.soc)*1000*fT;
  const Paux = Pcomp+PptcAir+PptcW+Pblower+300;
  const Pbatt = Pdrive + (driving||charging||occupied ? Paux : 0) - Pch;
  const I = Pbatt/Vp;
  const Ploss = I*I*0.06;
  S.soc = clamp(S.soc - Pbatt*dt/3600/60000, 0, 1);

  // ---- pin: nhiệt
  const UAp = 450*flowB+25;
  const Qbc = UAp*(S.Tb-S.Tcb);
  S.Tb += (Ploss - Qbc + 12*(Ta-S.Tb))/3.5e5*dt;
  const Qmix = serial ? 350*(S.Tcm-S.Tcb) : 0;
  S.Tcb += (Qbc - Qch + PptcW*0.95 + Qmix + 8*(Ta-S.Tcb))/7e4*dt;
  const spT = 1 + (Math.abs(Ploss)/1000 + Math.abs(Qbc)/2500)/(0.25+flowB);
  S.spread += (Math.min(spT, 15)-S.spread)*Math.min(1, dt/400);

  // ---- motor / EDS / két nước
  const loss = Math.abs(Pdrive)*0.09;
  const UAm = 70*flowM+5, UAi = 60*flowM+3;
  S.Tm += (loss*0.6 - UAm*(S.Tm-S.Tcm) + 4*(Ta-S.Tm))/4e4*dt;
  S.Tinv += (loss*0.4 - UAi*(S.Tinv-S.Tcm) + 2*(Ta-S.Tinv))/8e3*dt;
  const airRad = Math.min(1, vm/22+0.9*fanAct)*(serial ? 0.1 : 1);
  const Qrad = 600*airRad*Math.max(0.15, flowM)*(S.Tcm-Ta) + 10*(S.Tcm-Ta);
  S.Tcm += (UAm*(S.Tm-S.Tcm) + UAi*(S.Tinv-S.Tcm) - Qrad - Qmix)/5e4*dt;

  // ---- rò nước, năng lượng, cờ
  if(F.leak) S.level = Math.max(0, S.level - F.leak/100/3600*dt);
  S.eClim += (Pcomp+PptcAir+Pblower)*dt/3.6e6;
  S.fastLongT = charging && Pch>0 && fT<0.8 ? S.fastLongT+dt : charging ? S.fastLongT : 0;
  S.odo += vm*dt/1000;
  S.t += dt;

  // BDU heats with current squared, GPS moves with speed, energy counters
  S.Tbdu += ((S.Tb + 1.2e-4*I*I) - S.Tbdu)*Math.min(1, dt/300);
  const P12 = parked ? 6 : 300 + Pblower*0.1;
  S.eMot += Math.max(0, Pdrive)*dt/3.6e6; S.eDcdc += P12*dt/3.6e6; S.eTot += Math.max(0, Pbatt)*dt/3.6e6;
  S.dist += vm*dt/1000; if(driving) S.driveT += dt;
  S.head += 0.0006*dt*Math.sin(S.t/420);
  S.lat += vm*dt*Math.cos(S.head)/111320; S.lon += vm*dt*Math.sin(S.head)/(111320*Math.cos(S.lat*Math.PI/180));
  S.alt += grade*vm*dt;
  const fD = (Tmin<0 ? 0.4 : Tmin<10 ? 0.7 : 1)*(Tmax>50 ? 0.6 : 1);
  const mdot = 0.25*flowB, half = mdot>0.01 ? Qbc/(2*mdot*3500) : 0;
  const omega = vm/0.36*9;
  S.view = {phase:ph.type, Ta, v, mode, blower, recirc, set, coolReq, precond, pumpB, pumpM, flowB, serial,
    fanCmd, fanAct, comp:S.comp, chillerOpen, Qch, PptcAir, PptcW, Pcomp, Pch, I, derate, gas,
    Iallow: simChargePmax(S.soc)*1000*fT/Vp,
    torque: omega>5 ? clamp(Pdrive/omega, -150, 400) : 0,
    fT, Vp, Idis:600*fD, Idcdc:P12/13.8, pedal: driving ? clamp(Pdrive/200000*160, 0, 100) : 0, rpm: omega*60/(2*Math.PI),
    chgLeft: charging && Pch>0 ? (0.8-S.soc)*60/(Pch/1000)*60 : 0,
    rearDefrost: mode==='heat' && Ta<12 && driving && S.t<600,
    TcInTrue: S.Tcb-half, TcOutTrue: S.Tcb+half,
    Tvent: mode==='cool' ? S.Tev+2 : mode==='heat' ? S.Tcab+PptcAir/(230*air+1) : S.Tcab};
}

function simSample(){
  const S = SIM, w = S.view;
  const r = {t:S.t, vin:'SIM-'+simScnKey.toUpperCase(), scn:simScnKey,
    ts: new Date(simBase()+S.t*1000+7*3600e3).toISOString().slice(0,19).replace('T',' ')+'+07:00',
    phase:w.phase, v:w.v, odo:S.odo, soc:S.soc*100, park:S.park/60, Ta:w.Ta, Tcab:S.Tcab, mode:w.mode, set:w.set,
    blower:w.blower, recirc:w.recirc, Tev:S.Tev,
    TcIn: w.TcInTrue + (SIM_F.offset ?? 0), TcOut:w.TcOutTrue, TcInTrue:w.TcInTrue,
    Tmax:S.Tb+S.spread/2, Tmin:S.Tb-S.spread/2, Tpack:S.Tb, coolReq:w.coolReq, pumpB:w.pumpB, pumpM:w.pumpM,
    precond:w.precond, I:w.I, Pch:w.Pch/1000, Iallow:w.Iallow, fastLong:S.fastLongT>120,
    cold:(S.Tb-S.spread/2)<10 && w.phase!=='park', hot:(S.Tb+S.spread/2)>50,
    Tm:S.Tm, Tinv:S.Tinv, torque:w.torque, plim:w.derate, fanErr:S.fanErr, ptcErr:S.ptcErr, lowCool:S.level<0.7,
    eClim:S.eClim, faults:simFaultLabel(), comp:w.comp, Pcomp:w.Pcomp/1000, fanCmd:w.fanCmd, fanAct:w.fanAct,
    chillerOpen:w.chillerOpen, Qch:w.Qch, PptcAir:w.PptcAir, PptcW:w.PptcW, flowB:w.flowB, gas:w.gas,
    level:S.level, Tcm:S.Tcm, serial:w.serial, Tvent:w.Tvent,
    Vp:w.Vp, Tbdu:S.Tbdu, eMot:S.eMot, eDcdc:S.eDcdc, eTot:S.eTot, dist:S.dist, driveT:S.driveT,
    lat:S.lat.toFixed(6), lon:S.lon.toFixed(6), alt:S.alt, pedal:w.pedal, rpm:w.rpm, Idis:w.Idis, Idcdc:w.Idcdc,
    chgLeft:w.chgLeft, rearDefrost:w.rearDefrost, ts0:new Date(simBase()+7*3600e3).toISOString().slice(0,19).replace('T',' ')+'+07:00',
    tqF: drive==='rear' ? 0 : drive==='dual' ? w.torque/2 : w.torque, tqR: drive==='front' ? 0 : drive==='dual' ? w.torque/2 : w.torque,
    pumpFault: SIM_F.pump ?? null, valveFault: !!SIM_F.valve, fT:w.fT,
    fa: Object.keys(SIM_F).filter(k=>SIM_F[k]!==null && SIM_F[k]!==undefined && (SIM_FON[k] ?? 0) <= S.t)};
  simRows.push(r);
  detRun(r);
  simLiveLabels(r);
}

/* ---- gắn trạng thái mô phỏng vào mô hình 3D */
const SIM_LIVE = {
  battery:r=>`Pin ${r.Tmax.toFixed(1)}°C`, evaporator:r=>`Dàn lạnh ${r.Tev.toFixed(1)}°C`,
  motor:r=>`Motor ${r.Tm.toFixed(0)}°C`, inverter:r=>`EDS ${r.Tinv.toFixed(0)}°C`,
  chiller:r=>`Chiller ${r.Qch>50 ? (r.Qch/1000).toFixed(1)+' kW' : 'nghỉ'}`, compressor:r=>`Máy nén ${Math.round(r.comp*100)}%`,
  fan:r=>`Quạt ${Math.round(r.fanAct*100)}%${r.fanCmd>0.3 && r.fanAct===0 ? ' (lệnh '+Math.round(r.fanCmd*100)+'%)' : ''}`,
  radiator:r=>`Két ${r.Tcm.toFixed(0)}°C`, tank:r=>`Nước ${Math.round(r.level*100)}%`,
  blower:r=>`Blower mức ${r.blower}`, ptc_air:r=>`PTC gió ${(r.PptcAir/1000).toFixed(1)} kW`,
  ptc_water:r=>`PTC nước ${(r.PptcW/1000).toFixed(1)} kW`, batt_pump:r=>`Bơm pin ${r.pumpB ? 'chạy' : 'nghỉ'}`
};
function simLiveLabels(r){ Object.entries(SIM_LIVE).forEach(([id,f])=>{ if(labelOf[id]) labelOf[id].textContent = f(r); }); }
function simRestoreLabels(){ Object.keys(SIM_LIVE).forEach(id=>{ if(labelOf[id]) labelOf[id].textContent = COMPS[id].short; }); }

function simVisual(){
  const r = simRows[simRows.length-1]; if(!r) return;
  const comp = r.comp>0.05, cool = r.mode==='cool', heat = r.mode==='heat';
  Object.entries(PIPES).forEach(([id,mesh])=>{
    const cat = mesh.userData.cat; let on = false;
    if(cat==='data') on = true;
    else if(id==='r1' || id==='r2') on = comp;
    else if(['r2a','r4','r5'].includes(id)) on = comp && cool;
    else if(['r2b','r3','r6'].includes(id)) on = comp && r.chillerOpen;
    else if(GAS_HP.includes(id)) on = false;
    else if(BATT.includes(id)) on = r.pumpB;
    else if(id==='x1') on = r.serial && r.pumpM;
    else if(id==='m3' || id==='m4') on = r.pumpM && !r.serial;
    else if(MOTOR.includes(id)) on = r.pumpM;
    else if(cat==='air') on = r.blower>0 && (id==='a3c' ? cool : id==='a3h' ? heat : true);
    if(mesh.userData.on!==on){ mesh.material = on ? FMAT[cat].active : (cat==='air' ? idleAir : idlePipe); mesh.userData.on = on; }
  });
  fanTarget = r.fanAct; blowerTarget = r.blower/7;
  flapTarget = cool ? [0,0] : heat ? [Math.PI,Math.PI] : [Math.PI/2,Math.PI/2];
  agsTarget = (r.fanCmd>0.05 || comp) ? 1.25 : 0;
  const g = {};
  if(r.PptcAir>0) g.ptc_air = ['warm', Math.min(1, r.PptcAir/4000)];
  if(r.PptcW>0) g.ptc_water = ['warm', 0.9];
  if(r.Qch>100) g.chiller = ['cold', Math.min(0.8, r.Qch/3000)];
  if(comp && cool && r.Tev<12) g.evaporator = ['cold', 0.5];
  if(r.Tmax>40) g.battery = ['warm', Math.min(0.8, (r.Tmax-40)/12)]; else if(r.Tmin<10) g.battery = ['cold', Math.min(0.7, (10-r.Tmin)/10)];
  if(r.Tm>90) g.motor = ['warm', Math.min(0.9, (r.Tm-90)/60)];
  if(r.Tinv>60) g.inverter = ['warm', Math.min(0.9, (r.Tinv-60)/30)];
  if(r.fanCmd>0.3 && r.fanAct===0) g.fan = ['warm', 0.7];
  if(r.lowCool) g.tank = ['warm', 0.7];
  DET.forEach(d=>{ if(DET_ST[d.id] && DET_ST[d.id].ex && DET_ST[d.id].status===2) g[d.comp] = ['data', 0.9]; });
  glow = g;
}

function simFrame(dt){
  if(!simOn) return;
  if(simRunning){
    const T = simDuration(SIM_SCN[simScnKey]);
    simAcc += dt*simSpeed;
    let n = Math.min(2400, Math.floor(simAcc)); simAcc -= n;
    while(n-- > 0 && SIM.t < T){ simStep(1); if(SIM.t >= simNext){ simSample(); simNext += 10; } }
    if(SIM.t >= T){ simRunning = false; $('#simRun').textContent = 'Chạy lại'; simDraw(); simClock(); simToast(`Mô phỏng xong — ${simRows.length} dòng dữ liệu`); }
    else if(performance.now()-simDrawT > 250){ simDraw(); simClock(); simDrawT = performance.now(); }
  }
  simVisual();
}

/* ---- biểu đồ (SVG, cùng trục thời gian) */
function simNiceTicks(lo, hi, n){
  if(hi-lo < 1e-6) hi = lo+1;
  const raw = (hi-lo)/n, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw/p;
  const step = (m<1.5 ? 1 : m<3 ? 2 : m<7 ? 5 : 10)*p;
  const out = []; for(let v = Math.floor(lo/step)*step; v <= Math.ceil(hi/step)*step+step*1e-6; v += step) out.push(+v.toFixed(6));
  return out;
}
function simFmtT(s){ const h = Math.floor(s/3600), m = Math.floor(s%3600/60); return h ? `${h}h${String(m).padStart(2,'0')}` : `${m}′`; }
const simFmt = v => v==null || !isFinite(v) ? '–' : Math.abs(v)>=100 ? v.toFixed(0) : v.toFixed(1);
function simPath(rows, k, X, Y, stride){
  let d = '';
  for(let i=0; i<rows.length; i+=stride){ const v = rows[i][k]; if(v==null || !isFinite(v)) continue; d += (d ? 'L' : 'M') + X(rows[i].t).toFixed(1) + ' ' + Y(v).toFixed(1); }
  const last = rows[rows.length-1]; if(last && rows.length>1 && (rows.length-1)%stride) d += 'L' + X(last.t).toFixed(1) + ' ' + Y(last[k]).toFixed(1);
  return d;
}
function simNearest(t){
  let lo = 0, hi = simRows.length-1; if(hi<0) return null;
  while(lo<hi){ const mid = (lo+hi)>>1; if(simRows[mid].t < t) lo = mid+1; else hi = mid; }
  if(lo>0 && Math.abs(simRows[lo-1].t-t) < Math.abs(simRows[lo].t-t)) lo--;
  return simRows[lo];
}
function simBuildCharts(){
  $('#charts').innerHTML = SIM_CHARTS.map(c=>`<div class="chart">
    <div class="ch-head"><b>${c.title}</b><span>${c.unit}</span></div>
    <div class="legend2">${c.s.map(([,l,s])=>`<span><i style="--sw:var(--series-${s})"></i>${l}</span>`).join('')}${c.ref ? `<span><i class="dash"></i>${c.ref[1]}</span>` : ''}</div>
    <div class="ch-plot" id="ch_${c.id}"></div></div>`).join('');
  SIM_CHARTS.forEach(c=>{
    const host = $('#ch_'+c.id);
    host.addEventListener('pointermove', e=>{
      const m = host._meta; if(!m) return;
      const x = e.clientX - host.getBoundingClientRect().left;
      simCross(clamp((x-m.L)/m.pw, 0, 1)*m.T, host.id);
    });
    host.addEventListener('pointerleave', ()=>simCross(null));
  });
}
function simDraw(){
  if(!simOn) return;
  const sc = SIM_SCN[simScnKey], T = simDuration(sc), rows = simRows;
  const stride = Math.max(1, Math.ceil(rows.length/500));
  SIM_CHARTS.forEach(c=>{
    const host = $('#ch_'+c.id); if(!host) return;
    const W = Math.max(220, host.clientWidth), H = 132, L = 34, R = 34, Tp = 8, B = 18, pw = W-L-R, ph = H-Tp-B;
    const keys = c.s.map(x=>x[0]).concat(c.ref ? [c.ref[0]] : []);
    let lo = Infinity, hi = -Infinity;
    for(const r of rows) for(const k of keys){ const v = r[k]; if(v!=null && isFinite(v)){ if(v<lo) lo = v; if(v>hi) hi = v; } }
    if(!isFinite(lo)){ lo = 0; hi = 10; }
    if(c.unit==='kW') lo = Math.min(0, lo);
    const yt = simNiceTicks(lo, hi, 3), y0 = yt[0], y1 = yt[yt.length-1];
    const X = t=> L + t/T*pw, Y = v=> Tp + (1-(v-y0)/(y1-y0))*ph;
    let svg = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${c.title} theo thời gian mô phỏng">`;
    let acc = 0;
    sc.phases.forEach(p=>{
      const x0 = X(acc), x1 = X(Math.min(T, acc+p.dur));
      if(p.type!=='drive') svg += `<rect x="${x0.toFixed(1)}" y="${Tp}" width="${(x1-x0).toFixed(1)}" height="${ph}" fill="var(--band-${p.type})"/>`;
      if(c.id==='cb' && x1-x0 > 40) svg += `<text x="${(x0+3).toFixed(1)}" y="${Tp+9}" class="ph">${SIM_PH[p.type]}</text>`;
      acc += p.dur;
    });
    yt.forEach(v=>{ svg += `<line x1="${L}" x2="${L+pw}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" class="gl"/><text x="${L-5}" y="${(Y(v)+3.5).toFixed(1)}" class="yt">${+v.toFixed(1)}</text>`; });
    const xs = [60,300,600,900,1800,3600,7200,10800,21600].find(s=>T/s<=6) || 43200;
    for(let s = 0; s <= T+1; s += xs) svg += `<text x="${X(s).toFixed(1)}" y="${H-5}" class="xt">${simFmtT(s)}</text>`;
    if(c.ref && rows.length) svg += `<path d="${simPath(rows, c.ref[0], X, Y, stride)}" class="ref"/>`;
    if(rows.length) c.s.forEach(([k,,s])=>{ svg += `<path d="${simPath(rows, k, X, Y, stride)}" fill="none" stroke="var(--series-${s})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`; });
    const last = rows[rows.length-1];
    if(last){
      const ends = c.s.map(([k,,s])=>({y:Y(last[k]), v:last[k], s})).sort((a,b)=>a.y-b.y);
      for(let i=1; i<ends.length; i++) if(ends[i].y-ends[i-1].y < 11) ends[i].y = ends[i-1].y+11;
      const lx = X(last.t);
      ends.forEach(e=>{ svg += `<circle cx="${lx.toFixed(1)}" cy="${Y(e.v).toFixed(1)}" r="3.5" fill="var(--series-${e.s})" stroke="var(--surface)" stroke-width="1.5"/><text x="${(lx+6).toFixed(1)}" y="${(e.y+3.5).toFixed(1)}" class="ev">${simFmt(e.v)}</text>`; });
    }
    DET.filter(d=>d.chart===c.id && DET_ST[d.id] && DET_ST[d.id].alarm!==null).forEach((d,i)=>{ const x = X(DET_ST[d.id].alarm).toFixed(1);
      svg += `<line x1="${x}" x2="${x}" y1="${Tp}" y2="${Tp+ph}" class="dm"/><text x="${(+x+3).toFixed(1)}" y="${Tp+20+i*11}" class="dml">${d.bai}</text>`; });
    svg += `<line class="xh" x1="0" x2="0" y1="${Tp}" y2="${Tp+ph}" visibility="hidden"/></svg><div class="ctip" hidden></div>`;
    host.innerHTML = svg;
    host._meta = {L, pw, T, X, c};
  });
  simFlags();
  detRender();
}
function simCross(t, hostId){
  SIM_CHARTS.forEach(c=>{
    const host = $('#ch_'+c.id), m = host && host._meta; if(!m) return;
    const xh = host.querySelector('.xh'), tp = host.querySelector('.ctip');
    if(t==null || !simRows.length){ xh.setAttribute('visibility','hidden'); tp.hidden = true; return; }
    const r = simNearest(t), x = m.X(r.t);
    xh.setAttribute('x1', x); xh.setAttribute('x2', x); xh.setAttribute('visibility','visible');
    if(host.id!==hostId){ tp.hidden = true; return; }
    tp.innerHTML = `<b>${simFmtT(r.t)} · ${SIM_PH[r.phase]}</b><br>` +
      c.s.map(([k,l,s])=>`<i style="--sw:var(--series-${s})"></i>${l}: ${simFmt(r[k])} ${c.unit}`).join('<br>') +
      (c.ref ? `<br><i style="--sw:var(--muted)"></i>${c.ref[1]}: ${simFmt(r[c.ref[0]])} ${c.unit}` : '');
    tp.hidden = false;
    const w = tp.offsetWidth;
    tp.style.left = (x+10+w > host.clientWidth ? x-w-10 : x+10) + 'px';
  });
}
const SIM_FLAGS = [
  ['plim','Giới hạn công suất','34200.1.68','crit'], ['hot','Pin nóng','34200.1.31','crit'],
  ['lowCool','Thiếu nước làm mát','34200.7.1','crit'], ['fastLong','Sạc nhanh lâu hơn bình thường','34193.1.30','warn'],
  ['cold','Pin lạnh — giới hạn công suất','34220.1.93','warn'], ['fanErr','Lỗi quạt két (VCU)','34233.2.9','serious'],
  ['ptcErr','PTC lỗi','34233.2.198','serious']
];
function simFlags(){
  const r = simRows[simRows.length-1];
  const on = r ? SIM_FLAGS.filter(([k])=>r[k]) : [];
  $('#simFlags').innerHTML = on.length
    ? on.map(([,l,id,sev])=>`<span class="flag"><i style="--st:var(--st-${sev});color:var(--st-ink-${sev})" aria-hidden="true">!</i>${l} <code>${id}</code></span>`).join('')
    : `<span class="flag none">Không có cảnh báo trên telemetry ở thời điểm này</span>`;
}
function simClock(){
  if(!SIM) return;
  const r = simRows[simRows.length-1];
  $('#simTime').textContent = r ? r.ts.slice(11,16) : '--:--';
  $('#simPhase').textContent = `${SIM_PH[r ? r.phase : 'drive']} · đã chạy ${simFmtT(SIM.t)} / ${simFmtT(simDuration(SIM_SCN[simScnKey]))}`;
  $('#simRows').textContent = `${simRows.length} dòng dữ liệu`;
}

/* ---- xuất CSV */
function simCsv(){
  const esc = v=>{ if(typeof v==='number') return isFinite(v) ? String(+v.toFixed(2)) : ''; if(typeof v==='boolean') return v ? '1' : '0'; const s = String(v ?? ''); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
  const cols = simColumns();
  return [cols.map(c=>esc(c[0])).join(','), ...simRows.map(r=>cols.map(c=>esc(c[1](r))).join(','))].join('\n');
}
let simDl = null;
if(window.claude && typeof window.claude.use==='function') window.claude.use('downloads').then(d=>{ simDl = d; }).catch(()=>{});
async function simDownload(){
  if(!simRows.length){ simToast('Chưa có dữ liệu — bấm Chạy trước'); return; }
  const name = `mo_phong_${simScnKey}_${simRows.length}dong.csv`, data = '﻿' + simCsv();
  if(simDl){
    try{ await simDl.save({filename:name, data}); simToast('Đã lưu ' + name); }
    catch(e){ simToast(e && e.code==='declined' ? 'Đã hủy lưu file' : 'Không lưu được file' + (e && e.code ? ' ('+e.code+')' : '')); }
    return;
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([data], {type:'text/csv'})); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
  simToast('Đã tải ' + name);
}
let simToastT = 0;
function simToast(msg){ const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(simToastT); simToastT = setTimeout(()=>{ t.hidden = true; }, 3200); }

/* ---- giao diện */
function simOpenUI(){
  simOn = true;
  $('#path').hidden = true; $('#simview').hidden = false;
  $('#simOpen').setAttribute('aria-pressed', 'true');
  document.querySelectorAll('#modes .chip:not(.simbtn)').forEach(b=>{ b.disabled = true; });
  simBuildCharts(); simReadFaults(); simReset();
}
function simCloseUI(){
  simOn = false; simRunning = false;
  $('#path').hidden = false; $('#simview').hidden = true;
  $('#simOpen').setAttribute('aria-pressed', 'false');
  $('#simRun').textContent = 'Chạy';
  document.querySelectorAll('#modes .chip:not(.simbtn)').forEach(b=>{ b.disabled = false; });
  simRestoreLabels(); applyMode(mode);
}
$('#simScn').innerHTML = Object.entries(SIM_SCN).map(([k,v])=>`<option value="${k}">${v.label}</option>`).join('');
$('#faultGrid').innerHTML = SIM_FAULTS.map(f=>`<div class="fault"><input type="checkbox" id="f_${f.id}"><label for="f_${f.id}">${f.label} <span class="note">· bài ${f.probs}</span></label>${
  f.bool ? '' : `<input type="range" id="fv_${f.id}" min="${f.min}" max="${f.max}" step="1" value="${f.def}" aria-label="${f.label}"><span class="fv" id="fvt_${f.id}">${f.def} ${f.unit}</span>`}</div>`).join('');
$('#faultGrid').addEventListener('input', simReadFaults);
$('#simOpen').addEventListener('click', ()=> simOn ? simCloseUI() : simOpenUI());
$('#simClose').addEventListener('click', simCloseUI);
$('#simRun').addEventListener('click', e=>{
  if(!SIM || SIM.t >= simDuration(SIM_SCN[simScnKey])) simReset();
  simRunning = !simRunning;
  e.currentTarget.textContent = simRunning ? 'Tạm dừng' : 'Chạy tiếp';
});
$('#simReset').addEventListener('click', ()=>{ simRunning = false; $('#simRun').textContent = 'Chạy'; simReset(); });
$('#simScn').addEventListener('change', e=>{
  simScnKey = e.target.value; simSpeed = SIM_SCN[simScnKey].speed; $('#simSpeed').value = String(simSpeed);
  simRunning = false; $('#simRun').textContent = 'Chạy'; simReset();
});
$('#simSpeed').addEventListener('change', e=>{ simSpeed = +e.target.value; });
$('#simCsv').addEventListener('click', simDownload);
$('#simDets').addEventListener('click', e=>{ const b = e.target.closest('.det-name'); if(b) select(b.dataset.id); });
window.addEventListener('resize', ()=>{ if(simOn) simDraw(); });
