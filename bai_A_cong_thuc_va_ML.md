# Bài A – Công thức, đại lượng và hướng ML

> **Bài A:** Sạc chậm vì nhiệt → bộ phận nào đang yếu → sức khỏe bộ phận trong tương lai (phát biểu đầy đủ ở [plan, mục 3.A](VeHatI_Thermal_HVAC_Plan.md); cách giải từng bước ở [`bai_A_cach_giai.md`](bai_A_cach_giai.md)).
> Ba tầng = ba câu hỏi: **Tầng 1 phát hiện** (sạc chậm có do nhiệt không) → **Tầng 2 chẩn đoán** (bộ phận nào yếu: §4 khâu kém trong phiên + §5.4 gộp bằng chứng ra bộ phận) → **Tầng 3 dự báo** (sức khỏe bộ phận đó: §5.1–5.3, §6.4).
> Tài liệu này gom **mọi đại lượng và công thức** cần để làm bài: từ tín hiệu thô → chỉ số theo phiên → sức khỏe theo tuần → dự báo, kèm phần **ML** (mô hình gì, học từ đâu, đánh giá ra sao).
> Ngưỡng và hằng số ở đây là **giá trị khởi đầu**, chọn trên mô phỏng; phải chỉnh lại trên dữ liệu thật (mục 9).

---

## 0. Tổng quan

```
Telemetry (10 s/mẫu)
   │  §1 Tiền xử lý: sắp xếp, bỏ trùng, nội suy khe ngắn, làm mượt nhiệt, loại cảm biến sai
   ▼
§2 Tách PHIÊN sạc DC ──► đặc trưng phiên (SOC đầu/cuối, năng lượng, thời gian…)
   │
   ├─► §3 TẦNG 1 – PHÁT HIỆN: sạc chậm có do nhiệt không? ai hãm? nóng/lạnh? mất bao nhiêu phút?
   │        P_exp(t), r(t), minutes_lost
   │
   ├─► TẦNG 2 – CHẨN ĐOÁN: bộ phận nào đang yếu?
   │     §4  khâu kém trong phiên: ① τ_phản_ứng  ② ΔT_lạnh  ③ ε (↔ lưu lượng)  ④ k, a  ⑤ T_cân_bằng
   │         + tách phút mất: do bộ phận / do điều kiện
   │     §5.4 ghép dấu vết ngoài phiên (dàn lạnh, cờ) → bộ phận nghi ngờ + xác suất (Bayes), xác nhận qua nhiều phiên
   │
   └─► TẦNG 3 – DỰ BÁO: sức khỏe bộ phận đó trong tương lai
         §5.1–5.3 H_nguồn_lạnh / H_dòng_nước / H_tản theo tuần → xu hướng β → "còn bao lâu"; §6.4 lọc Kalman

§6 ML: thay ngưỡng / bảng tra bằng mô hình "mức đáng lẽ phải có" học từ xe khỏe; lọc Kalman cho xu hướng; về sau phân loại có nhãn
```

---

## 1. Ký hiệu và tín hiệu

| Ký hiệu | Ý nghĩa | Đơn vị | Tín hiệu | Mã |
|---|---|---|---|---|
| `t`, `Δt` | Thời điểm mẫu, khoảng lấy mẫu (≈ 10 s) | s | Timestamp | `34183.1.6` |
| `P(t)` | Công suất sạc | kW | Charging Power | `34220.1.118` |
| `I(t)` | Dòng pack (lấy trị tuyệt đối khi sạc) | A | Battery Pack Total Current | `34220.1.59` |
| `V(t)` | Điện áp pack | V | Pack Voltage | `34220.1.60` |
| `I_allow(t)` | Dòng sạc BMS cho phép tối đa | A | Continuous maximum allowable charge current | `34220.1.106` |
| `I_req(t)` | Dòng BMS yêu cầu trạm cấp | A | Charge Current Request | `34220.1.76` |
| `SOC(t)` | Mức pin | % | HV Battery SOC | `34183.1.9` |
| `T_max`, `T_min` | Nhiệt cell lớn nhất / nhỏ nhất | °C | Max / Min Cell Temperature | `34220.1.80` / `34220.1.78` |
| `T̄` | Nhiệt cell đại diện = (T_max + T_min) / 2 | °C | (tính) | — |
| `ΔT_cell` | Chênh nhiệt cell | °C | max and min cell temperature differences | `34220.1.81` |
| `T_in`, `T_out` | Nhiệt nước vào / ra tấm làm mát | °C | Battery Coolant Inlet / Outlet | `34220.1.104` / `34220.1.105` |
| `Q_req(t)` | BMS yêu cầu công suất làm mát | (kW, cần xác nhận) | requesting the cooling power… | `34220.1.109` |
| `pump(t)` | Trạng thái bơm pin | cờ | Battery electronic pump state | `34233.8.12` |
| `pre(t)` | Làm ấm pin trước khi sạc | cờ / mức | Battery pack precondition information | `34233.4.4` |
| `T_amb` | Nhiệt ngoài trời | °C | Ambient Temperature | `34183.1.7` |
| `chg`, `type`, `gun` | Đang sạc, loại sạc, súng DC | cờ | Charging status / type / DC gun | `34193.1.5` / `34193.1.32` / `34193.1.17` |
| `flag_long`, `flag_cold` | Nhãn tham khảo | cờ | Super Fast Charge Longer; Pack Power Degrade: cold | `34193.1.30`; `34220.1.93` |
| `T_ev` | Nhiệt dàn lạnh (dấu vết tầng 3) | °C | Actual evaporator temperature | `34233.9.39` |
| `E_pack` | Dung lượng pin khả dụng | kWh | Cấu hình dòng xe | — |

Chỉ số dưới `0` (ví dụ `k₀`) = giá trị **lúc xe khỏe** (mốc của chính xe đó). Chỉ số `std` = quy về **điều kiện chuẩn**.

---

## 2. Tiền xử lý và tách phiên

### 2.1 Làm sạch
```
1. Sắp xếp theo t, bỏ dòng trùng timestamp.
2. Đưa về lưới 10 s; khe ≤ 30 s → nội suy tuyến tính; khe > 30 s → đánh dấu, không nội suy qua.
3. Nhiệt độ (độ phân giải thường 1°C) → trung vị trượt 60 s để giảm bậc thang.
4. Loại cảm biến bị nghi sai (bước lọc cảm biến chung, plan mục 4.1):
     lúc xe đỗ ≥ 6 giờ: |T_in − median(T_max, T_min, T_out, T_pack)| > 3°C  → T_in không tin được
```

### 2.2 Đạo hàm nhiệt độ (dùng cho §4)
Không lấy hiệu hai mẫu liền nhau (bị bậc thang 1°C). Dùng **độ dốc hồi quy** trong cửa sổ `W` (mặc định 120 s):
```
dT̄/dt (t) = độ dốc của đường thẳng khớp {(τ, T̄(τ)) : |τ − t| ≤ W/2}
```

### 2.3 Tách phiên sạc DC
```
mẫu "đang sạc DC"  ⇔  chg = 1  ∧  gun = cắm  ∧  type = DC  ∧  P > 1 kW
phiên = chuỗi mẫu đang sạc DC liên tiếp (gộp các khe < 2 phút)
bỏ phiên: thời lượng < 5 phút, hoặc mất > 20% mẫu
```

**Đặc trưng phiên cơ bản:**
```
t_phiên   = Σ Δt                            (thời gian sạc thực)
E_nạp     = Σ P(t)·Δt                       (kWh)
ΔSOC      = SOC_cuối − SOC_đầu
T_max,đầu ; T_min,đầu ; T_max,đỉnh ; T_amb,TB ; P_max ; P_trạm (công suất tối đa trạm, nếu biết)
```

---

## 3. Tầng 1 – Ai hãm sạc, mất bao nhiêu phút

### 3.1 Công suất cho phép và công suất yêu cầu
```
P_allow(t) = V(t) · I_allow(t) / 1000          (kW)
P_req(t)   = V(t) · I_req(t)   / 1000
```

### 3.2 Ai đang giới hạn tại mỗi mẫu
```
TRẠM giới hạn   :  I(t) < 0,9 · I_req(t)                            (trạm không cấp đủ dòng BMS xin)
PIN giới hạn    :  I(t) ≥ 0,9 · I_req(t)  ∧  I_allow(t) < 0,9 · I_allow,ref(SOC)
   ├ vì NÓNG    :  T_max(t) > T_nóng      (khởi đầu 45°C)
   ├ vì LẠNH    :  T_min(t) < T_lạnh      (khởi đầu 15–20°C)
   └ khác       :  còn lại (SOC cao, lệch cell…) → không tính vào bài
```
`I_allow,ref(SOC)` = dòng cho phép của xe khỏe khi pin trong vùng tốt (20–35°C), học từ dữ liệu (§6.1).

### 3.3 Đường sạc chuẩn và công suất kỳ vọng
```
P_ref(SOC) = phân vị 90 { P | phiên của cùng dòng xe, SOC ∈ ô SOC, 20 ≤ T_min, T_max ≤ 35°C, trạm không giới hạn }
             (làm mượt, ép không tăng theo SOC)
P_exp(t)   = min( P_ref(SOC(t)), P_trạm )
r(t)       = P(t) / P_exp(t)
```
Giai đoạn 2 thay `P_ref` bằng mô hình M2 (§6.1).

### 3.4 Phiên bị giới hạn do nhiệt
```
thermally_limited = ∃ đoạn liên tục ≥ 2 phút có  r(t) < 0,85  ∧  PIN giới hạn vì NÓNG hoặc LẠNH
```

### 3.5 Số phút mất (tính theo từng mẫu)
Trong khoảng `Δt`, pin nạp được `P(t)·Δt`. Nếu sạc ở `P_exp` thì chỉ mất `P(t)·Δt / P_exp(t)`. Phần chênh là thời gian mất:
```
mất(t)            = Δt · (1 − P(t) / P_exp(t))                 (chỉ khi P(t) < P_exp(t))
minutes_lost_nóng = Σ_{t: hãm vì NÓNG} mất(t) / 60
minutes_lost_lạnh = Σ_{t: hãm vì LẠNH} mất(t) / 60
minutes_lost      = minutes_lost_nóng + minutes_lost_lạnh
```
Phần trạm giới hạn **không** tính (đã loại ở §3.2).

---

## 4. Tầng 2 – Hệ tản nhiệt có làm đúng việc không

**Mặt nạ "đang làm mát":**
```
A(t) = Q_req(t) > 0  ∧  pump(t) = bật
Đoạn làm mát = chuỗi A(t) liên tục; bỏ 5 phút đầu mỗi đoạn khi tính trung vị (giai đoạn chuyển tiếp)
```

### ① Độ trễ phản ứng
```
t₀      = lúc bắt đầu một đoạn làm mát
τ_resp  = min{ t − t₀ : T_in(t₀) − T_in(t) ≥ 3°C }
không_phản_ứng = (không tồn tại τ_resp trong 15 phút)  ∨  (Q_req > 0 mà pump = tắt kéo dài > 1 phút)
```

### ② Độ lạnh của nước (nguồn lạnh có đủ không)
```
ΔT_lạnh(t)   = T_max(t) − T_in(t)
ΔT_lạnh,phiên = median_{t ∈ A} ΔT_lạnh(t)
```
Xe khỏe khi làm mát mạnh: ≥ 7–10°C. Nhỏ nghĩa là **nước không được làm lạnh đủ** (chiller, gas, máy nén, quạt / dàn nóng).

### ③ Hiệu suất tấm làm mát ε (thay cho lưu lượng)
Tấm làm mát là bộ trao đổi nhiệt giữa cell và nước. Hiệu suất của nó:
```
ε(t) = (T_out − T_in) / (T̄ − T_in)              (0 < ε < 1)
```
Với bộ trao đổi nhiệt có hệ số truyền nhiệt `UA` không đổi:
```
ε = 1 − exp( −UA / (ṁ·c_p) )        ṁ: lưu lượng nước, c_p ≈ 3,5 kJ/(kg·K) với nước glycol
→  ṁ·c_p = UA / ( −ln(1 − ε) )
→  Chỉ số lưu lượng tương đối:   F = ṁ / ṁ₀ = ln(1 − ε₀) / ln(1 − ε)
```
- **Lưu lượng giảm** (bơm yếu, thiếu nước, có khí, tắc) → nước ở lâu trong tấm, ra gần bằng nhiệt cell → **ε tăng**, `F < 1`.
- **Nguồn lạnh yếu** chỉ làm `T_in` cao lên, **ε gần như không đổi**.

→ ε tách được "nước chảy kém" khỏi "nước không đủ lạnh". Cần `T̄ − T_in ≥ 3°C` mới tính, vì mẫu số nhỏ sẽ nhiễu.

Đi kèm: `ΔT_cell` tăng khi lưu lượng thấp.

### ④ Cân bằng nhiệt của pin: hệ số tản `k` và hệ số sinh nhiệt `a`
```
C · dT̄/dt = R·I² − UA_eff·(T̄ − T_in) − h·(T̄ − T_amb)

chia cho C:
dT̄/dt = a·I² − k·(T̄ − T_in) − b·(T̄ − T_amb)

a = R / C          (pin tự sinh nhiệt; tăng khi điện trở trong tăng = pin lão hóa)
k = UA_eff / C     (hệ tản lấy nhiệt khỏi pin; UA_eff = ṁ·c_p·ε, giảm khi lưu lượng / tiếp xúc kém)
b = h / C          (thất thoát ra vỏ; nhỏ)
```

**Ước lượng mỗi phiên** bằng hồi quy tuyến tính không âm (NNLS) trên các mẫu của phiên:
```
y  = dT̄/dt                                          (§2.2)
x₁ = I²       x₂ = −(T̄ − T_in)       x₃ = −(T̄ − T_amb)
min ‖y − (a·x₁ + k·x₂ + b·x₃)‖²   với a, k, b ≥ 0
```

**Chỉ nhận kết quả khi:**
- phiên ≥ 10 phút;
- `T̄` thay đổi ≥ 3°C;
- có cả đoạn làm mát;
- R² ≥ 0,5.

Lưu kèm sai số chuẩn của `k` để làm trọng số ở §5.

**Cách đọc:**
- `k` ↓ → **dòng nước / tấm làm mát** kém.
- Mức `T_in` cao → **nguồn lạnh** kém.
- `a` ↑ dần mà `k` bình thường → **pin lão hóa**, không phải hệ tản.

### ⑤ Nhiệt cân bằng và thời gian chạm ngưỡng
Giữ `I`, `T_in`, `T_amb` không đổi thì `T̄` tiến dần về:
```
T_eq = ( a·I² + k·T_in + b·T_amb ) / ( k + b )
T̄(t) = T_eq + (T̄₀ − T_eq)·e^{−(k+b)·t}

Nếu T_eq > T_nóng:   t_chạm = −ln( (T_nóng − T_eq) / (T̄₀ − T_eq) ) / (k + b)
```
`T_eq > 45°C` ở dòng sạc đang dùng nghĩa là BMS **chắc chắn phải hãm**, và giải thích được *vì sao* phiên chậm.

(Có thể thay `T̄` bằng `T_max` với `T_max ≈ T̄ + ΔT_cell/2` khi so ngưỡng.)

### Tách phút mất: do hệ tản / do điều kiện (phép "nếu như")
```
1. Học đường hãm của BMS:  f_T(T_max, T_min) = I_allow / I_allow,ref(SOC)    (từ dữ liệu, §6.1)
2. Mô phỏng lại phiên với HỆ TẢN KHỎE: k := k₀, T_in := T_in,exp(t) (mô hình M3a, §6.2), giữ nguyên I_req, T_amb, SOC đầu
     → T̄_cf(t), I_cf(t) = min(I_req, f_T(T_cf)·I_allow,ref), P_cf(t)
3. minutes_lost_điều_kiện = Σ Δt·(1 − P_cf/P_exp)/60      (vẫn mất dù hệ tản khỏe)
   minutes_lost_hệ_tản    = minutes_lost − minutes_lost_điều_kiện
```

### Kết luận theo phiên
```
binh_thuong        : ①②③④ trong khoảng của xe khỏe ở cùng điều kiện
khong_phan_ung     : ① xấu
nuoc_khong_du_lanh : ② xấu (ΔT_lạnh nhỏ / T_in cao) ∧ ε bình thường
nuoc_chay_kem      : ε cao (F < 0,7) ∨ k giảm rõ, kèm ΔT_cell tăng
lam_am_kem         : pin lạnh ∧ pre bật ∧ T_in không cao hơn T̄ ≥ 3°C sau 10 phút
khong_lam_am_truoc : pin lạnh ∧ pre chưa bật trước phiên
```
"Xấu" được định nghĩa bằng ngưỡng cứng ở giai đoạn 1, và bằng **điểm z so với mô hình xe khỏe** ở giai đoạn 2 (§6.3).

---

## 5. Tầng 3 – Sức khỏe linh kiện theo tuần

### 5.1 Chỉ số sức khỏe

Mỗi tuần, lấy **trung vị có trọng số** các phiên có làm mát. Trọng số = 1 / (sai số chuẩn của k)².
```
H_tản        = k_tuần / k₀                                      (dòng nước + tấm làm mát)
H_dòng_nước  = F_tuần = ln(1 − ε₀) / ln(1 − ε_tuần)             (lưu lượng tương đối)
H_nguồn_lạnh = ΔT_lạnh,std,tuần / ΔT_lạnh,std,₀                  (khả năng làm lạnh nước)
H_sinh_nhiệt = a₀ / a_tuần                                      (pin; < 1 = pin sinh nhiệt nhiều hơn)
```
- `ΔT_lạnh,std` = độ lạnh **quy về điều kiện chuẩn** bằng mô hình M3a: phần dư (thực − dự đoán) cộng vào giá trị dự đoán tại điều kiện chuẩn (35°C ngoài trời, 120 kW, BMS xin làm mát mạnh).
- Mốc `k₀, ε₀, ΔT_lạnh,std,₀, a₀` = trung vị **N = 10 phiên đầu** của xe (hoặc 30 ngày đầu). Xe mới chưa đủ phiên thì dùng **mốc của dòng xe**, rồi cập nhật dần.

### 5.2 Xu hướng và phát hiện thay đổi
```
β       = độ dốc Theil–Sen của H theo tuần             (chống điểm lạ)
CUSUM:  S_n = max(0, S_{n−1} + (H₀ − H_n) − κ);  báo "điểm gãy" khi S_n > h
```
- Điểm gãy **giảm đột ngột** = hỏng đột ngột (quạt chết…).
- Điểm gãy **tăng đột ngột** = vừa sửa / bảo dưỡng → **đặt lại mốc**, không kéo xu hướng xuyên qua.

### 5.3 Ngưỡng nguy hiểm và "còn bao lâu"
**Phiên chuẩn trưa hè:** T_amb = 35°C, dòng `I_std` (≈ 150 kW / V), `T_in,std` (từ M3a). Phiên này bị hãm khi `T_eq > 45°C`:
```
k_crit = a·I_std² / (45 − T_in,std)          (bỏ qua b)
H_crit = k_crit / k₀

Nếu β < 0:   ETA_tuần = (H_now − H_crit) / (−β)
Khoảng tin cậy: bootstrap theo tuần (lấy mẫu lại các tuần, tính lại β) → phân vị 10–90%
```
Tương tự cho `H_nguồn_lạnh`: tìm mức độ lạnh mà phiên chuẩn bắt đầu bị hãm.

### 5.4 Chẩn đoán linh kiện (gộp bằng chứng kiểu Bayes)
```
P(c | E) ∝ P(c) · Π_i P(e_i | c)
c ∈ {thieu_gas, may_nen, quat_ket, chiller_hoac_van_chiller, bom_pin, thieu_nuoc, van_4_nga, ptc_nuoc, cam_bien, pin_lao_hoa}
```

**Bằng chứng `e_i`** (nhị phân hoặc theo mức):

| Bằng chứng | Cách tính |
|---|---|
| e1 nước không đủ lạnh | `H_nguồn_lạnh` < 0,8 |
| e2 nước chảy kém | `H_dòng_nước` < 0,7 |
| e3 dàn lạnh cabin cũng ấm | Phần dư `T_ev` khi điều hòa chạy ổn định > 4°C |
| e4 cờ quạt | `34233.2.9` |
| e5 cờ thiếu nước | `34200.7.1` |
| e6 cờ máy nén | `34233.2.184` |
| e7 cờ van | `34233.2.11` |
| e8 nước vào nóng bất thường đầu phiên | `T_in − T̄` > 3°C khi Q_req = 0 |
| e9 cờ bơm | `34233.2.192` |
| e10 cờ PTC | `34233.2.198` |
| e11 pin sinh nhiệt nhiều hơn | `H_sinh_nhiệt` < 0,8 |
| e12 cảm biến | Kiểm tra lúc xe nguội (§2.1) |

- **`P(e|c)` ban đầu** lấy từ kiến thức kỹ thuật: thường đi kèm 0,8; đôi khi 0,4; hiếm 0,05.
- **`P(c)`** lấy theo tần suất lỗi ước đoán.
- **Học lại từ phiếu xưởng:** mỗi ca xác nhận cộng đếm vào phân phối Beta / Dirichlet, `P(e|c) = (n_e,c + α) / (n_c + α + β)`.

---

## 6. ML

**Nguyên tắc:**
1. **Không cần nhãn lỗi**: học **hành vi bình thường** từ xe / phiên khỏe, rồi đo phần chênh.
2. Mô hình **nhẹ, giải thích được** (hồi quy, gradient boosting có ràng buộc).
3. Luật ở §3–§5 luôn chạy song song làm mốc so sánh.

### 6.1 M2 – Công suất sạc kỳ vọng và đường hãm của BMS

| | Nội dung |
|---|---|
| Mục tiêu | `I_allow` (tốt hơn `P`, vì không bị trạm làm nhiễu) |
| Đặc trưng | SOC, T_max, T_min, T_amb, dòng xe, (phiên bản phần mềm BMS) |
| Dữ liệu học | Mẫu **không bị trạm giới hạn** của xe / phiên khỏe |
| Mô hình | LightGBM, ràng buộc đơn điệu: giảm theo SOC, giảm khi T_max > 40, tăng theo T_min khi T_min < 25 |
| Đầu ra | `I_allow,ref(SOC)` (đặt T trong vùng tốt) và **đường hãm** `f_T(T_max, T_min) = Î_allow(SOC, T) / Î_allow(SOC, T_tốt)` |
| Dùng ở | §3.2, §3.3 (`P_exp = min(V·Î_allow,ref, P_trạm)`), phép "nếu như" ở §4 |

### 6.2 M3 – Mô hình hành vi bình thường của hệ tản

| Mô hình | Dự đoán | Đặc trưng | Học từ | Phần chênh tăng dần nghĩa là |
|---|---|---|---|---|
| **M3a** | `T_in` (hoặc `ΔT_lạnh`) trong lúc làm mát | T_amb, Q_req, I², T̄, thời gian từ lúc bắt đầu làm mát, điều hòa cabin bật / tắt, nhiệt cài đặt cabin | Phiên khỏe (cùng dòng xe) | **Nguồn lạnh** yếu: chiller, gas, máy nén, quạt / dàn nóng |
| **M3b** | `ε` | I, Q_req, pump, T̄ − T_in | Phiên khỏe | **Dòng nước** kém: bơm, thiếu nước, tắc |
| **M3c** | `dT̄/dt` | I², T̄ − T_in, T̄ − T_amb, SOC | Phiên khỏe | Tổng hợp; phần chênh dương kéo dài → hệ tản không theo kịp |

**Cách học hai tầng** (đội xe + từng xe):
```
ŷ = f_đội_xe(x) + δ_xe            f: LightGBM hoặc hồi quy tuyến tính học trên toàn đội xe khỏe
                                   δ_xe: lệch riêng của xe, ước lượng từ N phiên đầu (trung bình phần dư)
z(t) = (y − ŷ) / σ(x)              σ: độ lệch chuẩn phần dư theo điều kiện (hoặc dùng hồi quy phân vị 10/90%)
```

### 6.3 Điểm bất thường của phiên
```
z_lạnh   = trung vị z của M3a trong đoạn làm mát
z_ε      = trung vị z của M3b
z_k      = (k − k₀) / SE(k)
S_phiên  = √( z_lạnh² + z_ε² + z_k² )         (hoặc Mahalanobis với hiệp phương sai học trên phiên khỏe)
bat_thuong ⇔ S_phiên > ngưỡng (đặt sao cho tỉ lệ báo trên xe khỏe ≤ 1%)
```
Tùy chọn: Isolation Forest trên vector đặc trưng phiên (mục 6.6) để bắt kiểu bất thường chưa lường trước.

### 6.4 Dự báo bằng lọc Kalman (xu hướng tuyến tính cục bộ)

Trạng thái `x = [H, β]` (mức sức khỏe, tốc độ đổi mỗi tuần):
```
Dự đoán:   H_n = H_{n−1} + β_{n−1}        β_n = β_{n−1}           (+ nhiễu quá trình Q)
Đo:        H_đo,n = H_n + nhiễu (phương sai R_n = SE² của phiên / tuần)
Cập nhật:  bộ lọc Kalman chuẩn → H_n, β_n và hiệp phương sai
ETA:       mô phỏng nhiều đường tương lai từ phân phối (H_n, β_n) → phân phối thời điểm H chạm H_crit
```
Ưu điểm so với hồi quy thẳng:
- tự cân nhắc phiên nào đáng tin;
- chạy được khi dữ liệu thưa;
- cho khoảng tin cậy tự nhiên.

Kết hợp CUSUM (§5.2) để đặt lại khi có điểm gãy.

### 6.5 Khi có nhãn (giai đoạn sau)

| Bài toán | Mô hình | Nhãn |
|---|---|---|
| Linh kiện nào hỏng | Gradient boosting đa lớp, đã hiệu chỉnh xác suất (calibration) | Phiếu xưởng / bảo hành |
| Xác suất hỏng trong 30 ngày | Hồi quy logistic / gradient boosting | Ngày sửa chữa |
| Thời gian tới khi hỏng | Mô hình sống còn (Cox, Weibull AFT) với biến H, β, tuổi xe, km, vùng | Ngày sửa chữa + xe chưa hỏng (bị cắt) |

Mô hình Bayes ở §5.4 là cầu nối: dùng ngay khi chưa có nhãn, rồi học dần.

### 6.6 Bảng đặc trưng theo phiên (đầu vào chung cho các mô hình)

| Nhóm | Đặc trưng |
|---|---|
| Điều kiện | T_amb TB, giờ trong ngày, tháng, vùng, loại / công suất trạm, SOC đầu, SOC cuối, có chạy xe trước khi sạc (phút) |
| Nhiệt pin | T_max đầu / đỉnh / cuối, T_min đầu, ΔT_cell TB / đỉnh, tốc độ tăng T̄ 10 phút đầu |
| Sạc | P_max, E_nạp, t_phiên, r TB, % thời gian bị hãm vì nóng / lạnh, minutes_lost |
| Hệ tản | τ_resp, ΔT_lạnh,phiên, ε, F, k, a, b, R² hồi quy, T_eq, % thời gian Q_req > 0, T_in thấp nhất đạt được |
| Ngữ cảnh khác | điều hòa cabin bật / tắt, T_ev TB (nếu bật), pre có bật trước phiên, cờ bật trong phiên |
| Xe | dòng xe, tuổi, odometer, phiên bản phần mềm BMS / VCU |

### 6.7 Chia dữ liệu, đánh giá, cạm bẫy

**Chia dữ liệu:**
- **theo xe** (GroupKFold: không để cùng một xe ở cả tập học và tập thử);
- **theo thời gian** (học trên quá khứ, thử trên tương lai);
- trên dữ liệu giả: **giữ riêng một số kiểu lỗi** không dùng khi chỉnh.

**Chỉ số đánh giá:**

| Mức | Chỉ số |
|---|---|
| Phiên (tầng 1) | Precision / recall "bị giới hạn do nhiệt"; MAE minutes_lost; MAE phần do hệ tản (so với nhãn "nếu như" của dữ liệu giả) |
| Phiên (tầng 2) | Đúng kiểu bất thường; tỉ lệ báo trên xe khỏe |
| Mô hình M2 / M3 | MAE, độ phủ khoảng phân vị trên phiên khỏe (80% khoảng phải chứa ≈ 80% điểm) |
| Xe × tuần (tầng 3) | Top-1 / top-2 linh kiện; **thời gian báo trước** (tuần); MAE của ETA; độ phủ khoảng tin cậy ETA; báo nhầm / 1000 xe-tháng |

**Cạm bẫy:**
1. **Mùa:** trời nóng làm `T_in`, `T_max` cao lên. Luôn so qua mô hình có `T_amb`, không so thô.
2. **Trạm sạc khác nhau:** dùng `I_allow` / `I_req` thay vì `P`.
3. **Cập nhật phần mềm** BMS / VCU đổi ngưỡng → đưa phiên bản phần mềm vào đặc trưng, đặt lại mốc khi đổi phiên bản.
4. **Độ phân giải 1°C và mẫu thưa** → chỉ tính `k`, `ε` trên đoạn đủ dài; luôn kèm sai số.
5. **Rò rỉ nhãn:** không đưa cột "sự thật" của dữ liệu giả (`_truth_*`) vào đặc trưng.
6. **Không tách được** chiller với van chiller (thiếu tín hiệu). Đầu ra ghi "chưa phân biệt được".

---

## 7. Đầu ra (tóm tắt trường)

| Mức | Trường chính |
|---|---|
| Phiên | `thermally_limited`, `limited_by`, `minutes_lost`, `minutes_lost_nong`, `minutes_lost_lanh`, `minutes_lost_do_he_tan`, `minutes_lost_do_dieu_kien`, `kieu`, `tau_resp`, `dT_lanh`, `epsilon`, `F`, `k`, `a`, `T_eq`, `S_phien` |
| Xe × tuần | `H_tan`, `H_dong_nuoc`, `H_nguon_lanh`, `H_sinh_nhiet`, `beta`, `eta_tuan [p10, p50, p90]`, `nghi_ngo [{linh_kien, p}]`, `bang_chung [...]` |

(Ví dụ JSON đầy đủ ở plan, mục 3.A.4.)

---

## 8. Kiểm tra nhanh trên mô phỏng 3D

Trang [`vinfast_thermal_3d.html`](vinfast_thermal_3d.html) → Mô phỏng vận hành → kịch bản **Trưa nắng TP.HCM**, tải CSV và tính thử:

| Bật lỗi | Kỳ vọng thấy |
|---|---|
| Không lỗi | `ΔT_lạnh` lớn, `ε` ổn định, `k ≈ k₀`, `minutes_lost` nhỏ, phần do hệ tản ≈ 0 |
| Chiller 15% | `ΔT_lạnh` nhỏ, `T_in` cao; `ε` gần như không đổi; minutes_lost tăng, chủ yếu do hệ tản |
| Bơm pin 40% | `ε` tăng (F < 1), `T_out − T_in` lớn, `ΔT_cell` tăng; `k` giảm |
| Gas 60% | `ΔT_lạnh` nhỏ **và** dàn lạnh cabin ấm (e1 + e3 → thiếu gas) |
| Quạt két chết | `ΔT_lạnh` nhỏ lúc sạc (xe đứng), có cờ quạt |
| Cảm biến nước vào +6°C | `T_in > T_out` khi đang làm mát (vô lý) → bị loại ở §2.1 trước khi tính |

Cột `_truth_*` trong CSV (lưu lượng thật, lượng gas, nhiệt nước vào thật…) dùng để **kiểm tra công thức**, không đưa vào thuật toán.

---

## 9. Bảng tham số khởi đầu

| Tham số | Giá trị đầu | Ở mục |
|---|---|---|
| Lưới lấy mẫu; nội suy tối đa | 10 s; 30 s | §2.1 |
| Cửa sổ làm mượt nhiệt; cửa sổ đạo hàm | 60 s; 120 s | §2.1–2.2 |
| Phiên tối thiểu; gộp khe | 5 phút; 2 phút | §2.3 |
| Trạm giới hạn | I < 0,9·I_req | §3.2 |
| T_nóng; T_lạnh | 45°C; 15–20°C | §3.2 |
| Ngưỡng tỉ lệ công suất; thời lượng | 0,85; 2 phút | §3.4 |
| Phản ứng: mức giảm T_in; thời hạn | 3°C; 15 phút | §4 ① |
| ΔT_lạnh khỏe | trung vị xe khỏe (mô phỏng 9,8°C), nghi khi < 80% (7,9°C) | §4 ② |
| ε: điều kiện tính; ngưỡng F | T̄ − T_in ≥ 3°C; F < 0,7 | §4 ③ |
| Hồi quy k: điều kiện nhận | ≥ 10 phút, T̄ đổi ≥ 3°C, R² ≥ 0,5 | §4 ④ |
| Số phiên làm mốc | 10 phiên / 30 ngày | §5.1 |
| Phiên chuẩn trưa hè | 35°C, ≈ 150 kW | §5.3 |
| Tỉ lệ báo cho phép trên xe khỏe | ≤ 1% phiên | §6.3 |
