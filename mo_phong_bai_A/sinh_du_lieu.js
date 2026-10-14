// Sinh dữ liệu cho bài A bằng đúng engine mô phỏng của trang 3D (sim_block.js), chạy không cần trình duyệt.
// Cách chạy:  node sinh_du_lieu.js            (dùng engine/sim_block.js và engine/signals.json đi kèm)
// Kết quả:    data/*.csv  (mỗi file = 1 phiên kịch bản, 10 giây / dòng, đủ cột telemetry + cột _truth_ để chấm)
const fs = require('fs'), path = require('path');
const SIM_SRC = process.argv[2] || path.join(__dirname, 'engine', 'sim_block.js');
const SIG_SRC = process.argv[3] || path.join(__dirname, 'engine', 'signals.json');
const src = fs.readFileSync(SIM_SRC, 'utf8');
const SIGNALS = JSON.parse(fs.readFileSync(SIG_SRC, 'utf8'));
const el = () => ({ innerHTML:'', textContent:'', value:'60', checked:false, hidden:false, style:{}, addEventListener(){}, setAttribute(){},
  querySelector(){ return el(); }, querySelectorAll(){ return []; }, getBoundingClientRect(){ return {left:0}; }, clientWidth:300 });
const ctx = { $: () => el(), document:{ querySelectorAll:()=>[], createElement:()=>el(), body:el() }, window:{ addEventListener(){} },
  labelOf:{}, COMPS:{}, PIPES:{}, GAS_HP:[], BATT:[], MOTOR:[], FMAT:{}, idleAir:null, idlePipe:null, performance:{ now:()=>0 },
  applyMode(){}, mode:'all', fanTarget:0, blowerTarget:0, flapTarget:[0,0], agsTarget:0, glow:{}, SIGNALS, drive:'dual', select(){} };
const api = new Function(...Object.keys(ctx), src + `
return { SIM_SCN, simDuration, simCsv, setKey:k=>{ simScnKey=k; }, setF:f=>{ SIM_F=f; },
         reset:simReset, step:simStep, sample:simSample, sim:()=>SIM };`)(...Object.values(ctx));

const OUT = path.join(__dirname, 'data'); fs.mkdirSync(OUT, {recursive:true});
const base = JSON.parse(JSON.stringify({init:api.SIM_SCN.hcm.init}));
const hcmAmb = api.SIM_SCN.hcm.amb;

function run(name, key, faults, opt){
  const sc = api.SIM_SCN[key];
  if(key === 'hcm'){                                   // cho phép đổi nhiệt ngoài trời và nhiệt pin ban đầu
    const Ta = opt && opt.Ta, dB = opt && opt.dB || 0;
    sc.amb = Ta ? (t => Ta + 1.0*Math.sin(t/7200*Math.PI)) : hcmAmb;
    sc.init = Object.assign({}, base.init, {b: base.init.b + dB, cb: base.init.cb + dB});
    sc.soc = opt && opt.soc || 0.42;
  }
  api.setKey(key); api.setF(faults || {}); api.reset();
  const T = api.simDuration(sc); let next = 10;
  while(api.sim().t < T){ api.step(1); if(api.sim().t >= next){ api.sample(); next += 10; } }
  fs.writeFileSync(path.join(OUT, name + '.csv'), '﻿' + api.simCsv());
  return name;
}

// "Phiên chuẩn nặng": trưa 36°C, xe vừa chạy xa (pin đã ấm thêm 4°C), sạc từ khoảng 19% lên 80%
const NANG = {Ta:36, dB:4, soc:0.25};

// 1) Các ca lỗi riêng lẻ (tầng 1 + tầng 2)
const cases = [
  ['hcm_khoe', 'hcm', {}], ['hcm_chiller_50', 'hcm', {chiller:50}], ['hcm_chiller_15', 'hcm', {chiller:15}],
  ['hcm_bom_pin_40', 'hcm', {pump:40}], ['hcm_gas_65', 'hcm', {gas:65}], ['hcm_quat_chet', 'hcm', {fan:true}],
  ['hcm_van_ket', 'hcm', {valve:true}], ['hcm_cam_bien_lech', 'hcm', {offset:6}],
];
cases.forEach(([n,k,f]) => run(n, k, f, NANG));
run('hn_khoe', 'hn', {}); run('hn_ptc_hong', 'hn', {ptc:true});

let seed = 7; const rnd = () => (seed = (seed*16807) % 2147483647) / 2147483647;
// 2) 20 phiên xe khỏe, thời tiết / nhiệt pin / SOC ngẫu nhiên → học "mức đáng lẽ phải có" (tầng 3)
for(let i = 1; i <= 20; i++) run(`khoe_${String(i).padStart(2,'0')}`, 'hcm', {}, {Ta: 30 + 9*rnd(), dB: -2 + 7*rnd(), soc: 0.20 + 0.14*rnd()});

// 3) Một xe bị RÒ GAS CHẬM: 12 tuần, mỗi tuần 1 phiên sạc trưa, thời tiết và cách dùng thay đổi (tầng 3)
const weeks = [];
for(let w = 1; w <= 12; w++){
  const gas = 100 - 4*(w-1);                           // lượng gas thật: 100 → 56 %
  const o = {Ta: 32 + 6*rnd(), dB: -1 + 6*rnd(), soc: 0.21 + 0.10*rnd()};
  run(`tuan_${String(w).padStart(2,'0')}`, 'hcm', gas < 100 ? {gas} : {}, o);
  weeks.push({tuan:w, gas_that:gas, Ta:+o.Ta.toFixed(1), dB:+o.dB.toFixed(1), soc_bat_dau:+o.soc.toFixed(2)});
}
fs.writeFileSync(path.join(OUT, 'tuan_su_that.json'), JSON.stringify(weeks, null, 1));

// 4) Phiên chuẩn nặng với lượng gas giảm dần → tìm ngưỡng nguy hiểm (tầng 3)
for(let gas = 100; gas >= 50; gas -= 5) run(`chuan_gas_${gas}`, 'hcm', gas < 100 ? {gas} : {}, NANG);

console.log('xong:', fs.readdirSync(OUT).length, 'file trong', OUT);
