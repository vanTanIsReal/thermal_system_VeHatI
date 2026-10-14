# Thiết kế dữ liệu giả cho 3 bài chốt (A · B · C)

> Tài liệu này mô tả **cách sinh dữ liệu telemetry giả** sao cho giống xe thật: bộ phận hoạt động thế nào, bộ điều khiển quyết định ra sao, cảm biến đo và gửi tín hiệu thế nào, lỗi tác động vào đâu, và nhãn đúng được tạo ra sao.
> Đi kèm [kế hoạch v2](VeHatI_Thermal_HVAC_Plan.md) (mục 5.2). Nền tảng là engine mô phỏng đang chạy trong [`vinfast_thermal_3d.html`](vinfast_thermal_3d.html) ("Mô phỏng vận hành"), sẽ port sang Python và mở rộng ra cả đội xe.
> **Mọi tham số là giả định kỹ thuật hợp lý, chưa hiệu chuẩn theo xe VinFast.** Chúng được ghi ở một chỗ (mục 9) để chỉnh khi có dữ liệu thật hoặc dữ liệu công khai.

---

## 1. Nguyên tắc

1. **Lỗi tác động vào vật lý, không sửa thẳng vào tín hiệu.**
   - Ví dụ: két bẩn → giảm khả năng tản nhiệt của két → nước motor nóng hơn → motor nóng hơn → cảm biến đo được → cờ bật nếu vượt ngưỡng.
   - Thuật toán phát hiện chỉ thấy tín hiệu, giống hệt ngoài đời.
   - Ngoại lệ duy nhất là **lỗi cảm biến**, vốn nằm ở lớp đo.
2. **Bốn lớp tách bạch**, mỗi lớp chỉ đọc lớp trên:

```
 Điều kiện ─► Bộ điều khiển ─► Bộ phận ─► Trạng thái vật lý ─► Cảm biến ─► ECU ─► Telemetry ─► CSV/Parquet
 (thời tiết,   (CCU, BMS,      (máy nén,   (nhiệt pin, cabin,  (nhiễu, trễ,  (ngưỡng,  (lấy mẫu,
  lịch trình,   VCU)            bơm, quạt,   motor, nước, gas…)  làm tròn,     cờ, max/  mất gói,
  cách lái)                     PTC…)                             lệch)         min)      ngủ khi đỗ)
        ▲                          ▲
        └── mỗi xe một bộ tham số ─┘── lỗi làm đổi tham số bộ phận theo thời gian
```

3. **Mỗi xe khác nhau một chút** (sai số sản xuất, mức mòn) để ngưỡng cứng không quá dễ thắng.
4. **Nhãn đúng sinh bằng phép "nếu như"** (counterfactual): chạy lại cùng tình huống với xe khỏe để biết lỗi gây ra bao nhiêu (mục 7). Đây là cách có nhãn chính xác cho "số phút mất" (A) và "do hệ làm mát kém" (B).
5. **Chỉ xuất các cột có trong từ điển** (299 tín hiệu của [`thermal_hvac_signals.csv`](thermal_hvac_signals.csv)). Đại lượng ẩn (lượng gas, lưu lượng bơm, độ bẩn két…) chỉ nằm trong bảng "sự thật" riêng để kiểm tra, không lẫn vào dữ liệu đầu vào.

---

## 2. Đội xe và cách dùng xe

### 2.1 Đội xe (khoảng 200 xe × 180 ngày)

| Thuộc tính | Giá trị | Ghi chú |
|---|---|---|
| Dòng xe | 3 cấu hình: SUV 1 motor, SUV 2 motor, SUV lớn 2 motor | Khác khối lượng, công suất, dung lượng pin, có / không EDS sau |
| Sưởi | PTC (mặc định); heat pump 0–20% xe | Chỉ bật heat pump khi team xác nhận dòng nào có |
| Vùng | Hà Nội 45%, TP.HCM 45%, Đà Nẵng 10% | Hà Nội có mùa đông (bài C, A mùa lạnh); Đà Nẵng có đèo (bài B) |
| Thời gian | 180 ngày, nên bắt đầu khoảng tháng 11 | Phủ được cả mùa đông miền Bắc và đầu mùa nóng |
| Tuổi xe lúc bắt đầu | 0–3 năm | Ảnh hưởng mức mòn ban đầu |

### 2.2 Kiểu người dùng (mỗi xe gán một kiểu)

| Kiểu | Tỉ lệ | Lịch trình điển hình | Sạc |
|---|---|---|---|
| Đi làm | 50% | 2 chuyến / ngày × 20–40 phút, cuối tuần đi chơi | Chủ yếu AC ở nhà ban đêm; DC nhanh 1–2 lần / tuần |
| Dịch vụ (taxi, giao hàng) | 25% | 8–12 giờ / ngày, nhiều chuyến ngắn, đứng chờ có bật điều hòa | **DC nhanh 1–3 lần / ngày**, thường ngay sau khi chạy (pin nóng) → nhiều dữ liệu cho bài A |
| Đường dài | 25% | Ít chuyến nhưng dài; cao tốc, đèo (Hải Vân, Tam Đảo, Bảo Lộc) | DC nhanh giữa chuyến |

**Cách lái** (theo người): mức tăng tốc, tốc độ cao tốc, thói quen bật điều hòa sớm hay muộn, nhiệt cài đặt (21–26°C), tỉ lệ có làm ấm pin trước khi sạc mùa đông (0–80%).

### 2.3 Lịch trình một ngày

Mỗi ngày của mỗi xe là một chuỗi **pha**:

```
đỗ qua đêm (sạc AC?) → chuyến sáng → đỗ ở công ty (nắng?) → chuyến chiều → [sạc DC nhanh] → đỗ → ...
```

| Pha | Sinh như thế nào |
|---|---|
| **Chạy** | Ghép các đoạn đường: phố (dừng–chạy, 0–50 km/h), ngoại ô (40–70), cao tốc (80–110), **đèo** (dốc 6–10%, 40–70 km/h). Tốc độ có tăng / giảm tốc theo cách lái. Độ dốc từ tuyến đường. |
| **Sạc DC nhanh** | Chọn trạm (mục 3.6): 30 / 60 / 120 / 150 / 250 kW. Sạc tới 80–90% SOC hoặc tới khi người dùng rút (30–50 phút). Có thể bật điều hòa khi ngồi chờ. |
| **Sạc AC** | 7–11 kW, ban đêm ở nhà; ít ảnh hưởng nhiệt. |
| **Đỗ** | Pin, motor nguội dần theo môi trường; cabin nóng lên dưới nắng (có thể lên 55–65°C trưa hè). Bơm / quạt có thể chạy thêm vài phút sau khi tắt máy. |

### 2.4 Thời tiết

- **Nhiệt độ ngoài trời theo giờ** = trung bình tháng của thành phố + biên độ ngày (thấp nhất khoảng 5 giờ sáng, cao nhất khoảng 14 giờ) + dao động ngẫu nhiên theo ngày (đợt nóng, đợt rét).
- **Nắng (W/m²):** theo giờ trong ngày × độ mây; mưa thì nắng thấp.
- **Độ ẩm:** chỉ dùng để quyết định sấy kính (bài C).

| Thành phố | Tháng 1 (thấp / cao) | Tháng 4 | Tháng 6 |
|---|---|---|---|
| Hà Nội | 14 / 19°C, đợt rét 7–10°C | 22 / 28°C | 27 / 33°C, đợt nóng 38–40°C |
| TP.HCM | 22 / 31°C | 26 / 35°C | 25 / 32°C |
| Đà Nẵng | 19 / 24°C | 23 / 30°C | 26 / 35°C |

(Giá trị khí hậu tham khảo, làm tròn; chỉnh lại theo số liệu khí tượng nếu cần.)

---

## 3. Các bộ phận hoạt động như thế nào

Mỗi khối nhiệt dùng **mô hình một nút** (lumped): nhiệt vào − nhiệt ra = khối nhiệt × tốc độ tăng nhiệt.

```
C · dT/dt = Σ Q_vào − Σ Q_ra          bước tính dt = 1 giây (xuất mẫu mỗi 10 giây)
```

### 3.1 Xe chạy: công suất kéo và nhiệt sinh ra

```
P_bánh = m·g·(Crr + dốc)·v + ½·ρ·CdA·v³ + m·a·v
P_điện = P_bánh / η_truyền_động        (khi tăng tốc)      ·  P_điện = P_bánh · η_tái_sinh   (khi phanh tái sinh)
Nhiệt motor   = P_điện · (1 − η_motor)        η_motor ≈ 0,92–0,95 (thấp hơn ở mô-men lớn, tốc độ thấp)
Nhiệt inverter = P_điện · (2–3%)
Mô-men = P_bánh / tốc độ quay bánh              → tín hiệu mô-men thực `34233.3.148 / .153`
```

- Xe 2 motor chia mô-men trước / sau (khoảng 40 / 60 khi tăng tốc mạnh, phần lớn dồn một trục khi đi đều).
- **Leo đèo** là nơi sinh nhiệt motor lớn nhất, kéo dài: nguồn chính của bài B.

### 3.2 Pin

**Điện:**
```
Điện áp pin ≈ OCV(SOC) − I·R              I = P_pin / V
SOC giảm / tăng theo năng lượng
```

**Nhiệt sinh trong cell:**
```
Q_pin = I² · R(T, SOC)            R tăng mạnh khi lạnh:  R(T) = R25 · exp(k·(1/T − 1/298))
```

→ Mùa đông pin lạnh vừa sinh nhiệt nhiều hơn, vừa bị BMS hạn chế dòng (bài A, C).

**Nhiệt pin** (hai nút: khối cell và nước tấm làm mát):
```
C_pin · dT_pin/dt  = Q_pin − UA_tấm·(T_pin − T_nước_pin) − UA_vỏ·(T_pin − T_ngoài)
C_nước · dT_nước/dt = UA_tấm·(T_pin − T_nước_pin) − Q_chiller + Q_PTC_nước + Q_trao_đổi_van − tổn thất ra môi trường
UA_tấm = UA_tấm_max · f(lưu lượng bơm pin)
```

**Chênh nhiệt giữa các cell:** pin có khoảng 24–48 đầu đo.
- Mỗi đầu đo = nhiệt khối pin + **độ lệch vị trí** (cố định theo xe, ±1–2°C; cell gần đầu nước vào mát hơn) + phần tăng thêm khi dòng lớn, lưu lượng thấp.
- **Cell lớn nhất / nhỏ nhất** là max / min của các đầu đo → tín hiệu `34220.1.80 / .78`.
- Lưu lượng bơm giảm thì chênh nhiệt tăng: dấu hiệu bơm yếu (bài A).

**Nhiệt nước vào / ra pin:**
```
T_ra − T_vào = Q_tấm / (lưu_lượng · c_nước)
```
Lưu lượng thấp → chênh lớn: dấu hiệu bơm yếu / thiếu nước.

### 3.3 Vòng gas lạnh (máy nén, dàn nóng, van tiết lưu, dàn lạnh, chiller)

Không mô phỏng chi tiết áp suất (telemetry cũng không có). Dùng **khả năng làm lạnh tối đa**:

```
Q_lạnh_max = Q_định_mức · f_gas(lượng gas) · f_dàn_nóng(gió qua dàn nóng, độ bẩn) · f_ngoài(T_ngoài)
f_gas ≈ 1 khi gas ≥ 90%, giảm nhanh dưới 70%, ≈ 0 dưới 45%
gió qua dàn nóng = min(1, v/80 km/h + 0,9·quạt)       → xe đứng yên phụ thuộc hoàn toàn vào quạt
Q_lạnh = mức chạy máy nén (0–1, do CCU/BMS quyết định) · Q_lạnh_max
P_máy_nén = Q_lạnh / COP,  COP ≈ 2–3,5 (giảm khi trời nóng, khi dàn nóng thiếu gió)
```

**Chia lạnh cho hai nhánh:**
- **Chiller:** `Q_chiller = min(phần được chia, UA_chiller · hiệu_suất_chiller · (T_nước_pin − T_bay_hơi))`
- **Dàn lạnh cabin:** phần còn lại; nhiệt dàn lạnh (`34233.9.39`) cân bằng giữa lạnh từ gas và nhiệt của gió đi qua.

**Ghép cặp quan trọng:**
- Dàn nóng và két nước **đứng chung luồng gió đầu xe**: két / dàn nóng bẩn hoặc quạt chết ảnh hưởng **cả điều hòa lẫn motor**.
- Điều hòa cabin và làm mát pin **chung một máy nén**: khi sạc nhanh giữa trưa, hai nhánh tranh nhau.

### 3.4 Vòng nước motor và két nước

```
C_motor · dT_motor/dt = Nhiệt_motor − UA_motor·f(lưu_lượng)·(T_motor − T_nước_motor)
C_inv   · dT_inv/dt   = Nhiệt_inverter − UA_inv·f(lưu_lượng)·(T_inv − T_nước_motor)
C_nước  · dT_nước/dt  = (nhận từ motor + inverter + OBC/DC-DC) − Q_két − Q_trao_đổi_van
Q_két = UA_két · độ_sạch_két · f(gió qua két) · f(lưu_lượng) · (T_nước_motor − T_ngoài)
```

- **Van chia nước:** chế độ song song (hai vòng riêng) hoặc nối tiếp (nước motor đi qua pin để làm ấm pin, bỏ qua két).
- **Bơm motor:** lưu lượng theo lệnh VCU × độ khỏe bơm × hệ số khí lọt (khi thiếu nước).

### 3.5 Hộp HVAC và cabin

```
C_cabin · dT_cabin/dt = UA_vỏ·(T_ngoài − T_cabin) + nắng·hệ_số_kính + 80–120 W/người + Q_gió
Q_gió = lưu lượng gió · (T_gió_ra − T_cabin)
lưu lượng gió = mức gió (1–8) · độ thông của lọc gió
T_gió_ra: làm mát ≈ T_dàn_lạnh + 2°C;  sưởi = T_gió_vào + P_PTC_gió / (lưu lượng · c_không_khí) · tỉ lệ cửa trộn
```

- **Gió hồi:** lấy gió trong cabin (mát nhanh hơn khi nóng) hoặc gió ngoài.
- **Cửa gió trộn:** 0 = toàn lạnh, 1 = toàn nóng.
- **Đỗ nắng:** cabin tăng tới 55–65°C. Khi bật điều hòa, nhiệt cabin hạ theo đường cong hàm mũ, khoảng 10–20 phút về gần nhiệt cài đặt.

### 3.6 Trạm sạc và đường sạc

```
P_sạc = min( P_trạm · hệ_số_trạm ,  V_pin · I_cho_phép(SOC, T_min, T_max) )
```

- **Hệ số trạm:** 1 với trạm tốt; 0,5–0,8 với trạm yếu hoặc trạm chia công suất (10–15% số lần sạc).
- **Phần do trạm** giúp kiểm tra nhánh `khong_do_nhiet` của bài A.
- **Đường sạc chuẩn theo SOC:** phẳng tới khoảng 50% rồi giảm dần; mỗi dòng xe một đường. Có thể hiệu chỉnh hình dạng theo bộ đường sạc công khai (kế hoạch, mục 5.3).

### 3.7 Bộ phận phụ khác

| Bộ phận | Hoạt động | Ảnh hưởng |
|---|---|---|
| Bình nước phụ + cảm biến mức | Mức nước giảm khi rò; dưới khoảng 60% thì khí lọt vào vòng, lưu lượng bơm giảm | Cờ thiếu nước `34200.7.1`; nhiệt tăng (A, B) |
| AGS | Mở khi cần làm mát (nước motor nóng, máy nén chạy, xe chậm); đóng khi chạy nhanh và mát | Kẹt đóng → thiếu gió qua két và dàn nóng |
| Sấy kính sau, sưởi ghế | Điện trở, bật theo lệnh | Tốn điện, không qua HVAC (C) |
| OBC, DC-DC | Sinh nhiệt nhỏ vào vòng nước motor (OBC khi sạc AC) | Phụ |

---

## 4. Bộ điều khiển quyết định thế nào

Đây là phần làm dữ liệu "có hành vi", không chỉ là vật lý thụ động. Ngưỡng là giả định; **mỗi xe lệch ngẫu nhiên nhỏ** để tránh mọi xe giống hệt.

### 4.1 CCU (điều hòa)

| Quyết định | Luật |
|---|---|
| Chế độ | Bật khi có người trong xe (chạy / ngồi chờ khi sạc / bật từ xa). Làm mát nếu cabin > cài đặt + 1; sưởi nếu cabin < cài đặt − 1 và trời < 20°C |
| Mức gió | Tự động: 2 + |cabin − cài đặt| / 2,5, giới hạn 1–8; người dùng có thể chỉnh tay |
| Máy nén (nhánh cabin) | Mục tiêu dàn lạnh 3–5°C; giảm dần khi cabin gần cài đặt; **chống đóng băng**: dàn lạnh < 1°C thì giảm |
| Gió hồi | Bật khi cabin nóng hơn cài đặt > 3°C |
| PTC gió | Công suất tỉ lệ với khoảng thiếu nhiệt, tối đa 4–6 kW |
| Cửa trộn | Làm mát toàn lạnh, gần cài đặt thì trộn; sưởi toàn nóng |
| Sấy kính trước | Trời lạnh và ẩm, mấy phút đầu chuyến |

### 4.2 BMS (pin)

| Quyết định | Luật |
|---|---|
| **Yêu cầu làm mát** `34220.1.109` | Tăng khi cell lớn nhất > 35°C (đang sạc: > 32°C); mức yêu cầu tỉ lệ với khoảng vượt |
| **Yêu cầu làm ấm** | Cell nhỏ nhất < 15°C và (đang sạc nhanh hoặc đang làm ấm trước khi sạc) |
| **Dòng sạc cho phép** `34220.1.106` | Bảng theo SOC × nhiệt: giảm khi cell lớn nhất > 45°C (về khoảng 25% ở 53°C); giảm mạnh khi cell nhỏ nhất < 20°C (khoảng 15% ở 0°C) |
| **Dòng xả cho phép** `34220.1.107` | Giảm khi pin rất lạnh hoặc > 50°C |
| Cờ / cảnh báo | Pin nóng (> 50°C), pin lạnh (< 10°C), chênh nhiệt cell lớn, sạc lâu (`Super Fast Charge Longer` khi bị giới hạn do nhiệt > 2 phút) |

### 4.3 VCU (bơm, quạt, van, giới hạn công suất)

| Quyết định | Luật |
|---|---|
| Bơm pin | Chạy khi xe chạy, đang sạc, hoặc có yêu cầu làm mát / làm ấm |
| Bơm motor | Chạy khi xe chạy, đang sạc, hoặc nước motor > 45°C |
| **Quạt két** | Theo nước motor (bắt đầu ở 42°C, tối đa ở 57°C); tối thiểu 35–60% khi máy nén chạy; 80% khi xe đứng mà máy nén chạy mạnh |
| AGS | Mở theo nhu cầu quạt / máy nén; đóng khi > 80 km/h và mát |
| Van chia nước | Nối tiếp khi pin cần ấm và nước motor ấm hơn nước pin > 5°C; còn lại song song |
| **Giới hạn công suất** (bài B) | Motor > 130°C, hoặc inverter > 90°C, hoặc cell lớn nhất > 52°C → giảm công suất (ví dụ còn 50%), có **trễ**: bật khi vượt ngưỡng, tắt khi xuống dưới ngưỡng − 5°C |

---

## 5. Cảm biến và tín hiệu được sinh ra thế nào

### 5.1 Mô hình cảm biến

Mỗi tín hiệu đo được đi qua các bước:

```
giá trị thật → trễ cảm biến (lọc bậc 1, hằng số τ) → + lệch cố định của xe + nhiễu
            → làm tròn theo độ phân giải → [lỗi cảm biến nếu có] → ECU xử lý → lấy mẫu telemetry
```

| Tín hiệu | Mã | Giá trị thật lấy từ | τ trễ | Nhiễu σ | Làm tròn | Đặc điểm riêng |
|---|---|---|---|---|---|---|
| Nhiệt ngoài trời | `34183.1.7` | Không khí ngoài | 60 s | 0,3°C | 0,5°C | Đặt sau cản trước: **xe đứng nắng / kẹt xe đọc cao hơn thật 2–5°C** (nhiệt mặt đường, két) |
| Nhiệt cabin | `34183.1.15` | Nút cabin | 30 s | 0,2°C | 0,5°C | Nắng chiếu thẳng làm đọc cao hơn ~1°C |
| Nhiệt dàn lạnh | `34233.9.39` | Nút dàn lạnh | 5 s | 0,2°C | 0,5°C | Phản ứng nhanh khi máy nén bật / tắt |
| Nước vào / ra pin | `34220.1.104 / .105` | Nút nước pin ± ½ chênh | 10 s | 0,2°C | 0,5°C | Không lưu lượng thì cảm biến chỉ đo nước đứng yên |
| Cell lớn nhất / nhỏ nhất | `34220.1.80 / .78` | Max / min của 24–48 đầu đo | 20 s | 0,3°C mỗi đầu | **1°C** | Thường làm tròn 1°C; kèm số hiệu đầu đo `.77 / .79` |
| Chênh nhiệt cell | `34220.1.81` | Max − min | — | — | 1°C | Suy ra từ hai giá trị trên |
| Nhiệt motor | `34233.3.231` | Nút motor (cuộn stator) | 10 s | 0,5°C | 1°C | |
| Nhiệt EDS | `34233.3.232` | Nút inverter | 5 s | 0,5°C | 1°C | Cần xác nhận ý nghĩa |
| Công suất sạc | `34220.1.118` | V × I | — | 0,5% | 0,1 kW | |
| SOC | `34183.1.9` | SOC | — | — | 0,1–1% | |
| Mô-men, tốc độ, ga | `34233.3.148/.153`, `34183.1.2`, `34183.1.26` | Mô hình xe | — | nhỏ | theo đơn vị | |

(Độ phân giải, τ và nhiễu là giả định điển hình của cảm biến NTC và tín hiệu CAN; chỉnh khi có dữ liệu thật.)

### 5.2 Cờ, trạng thái và cảnh báo

- **Cờ ngưỡng** (cảnh báo nóng, lạnh, quá nhiệt nước EDS…) có **lọc thời gian** (phải vượt ngưỡng ≥ 2–5 s) và **trễ** (tắt ở ngưỡng thấp hơn), giống ECU thật. Không bật / tắt liên tục.
- **Trạng thái bơm** (`34233.8.12 / .11`): bật / tắt theo lệnh VCU. **Không phản ánh bơm yếu**, chỉ phản ánh có chạy hay không. Đây là lý do bài A phải suy bơm yếu từ chênh nhiệt.
- **Cờ lỗi bộ phận** (quạt, van, PTC, EAC, bơm): chỉ bật khi **bộ phận hỏng hẳn và ECU tự phát hiện được** (quạt không quay khi có lệnh, PTC không ăn dòng). Hỏng từ từ (két bẩn, gas rò chậm, chiller đóng cặn) **không có cờ**. Đây là phần các bài toán phải tự phát hiện.
- **Đèn báo giới hạn công suất** `34200.1.68`: bật khi VCU giới hạn (mục 4.3).

### 5.3 Lớp telemetry (gửi lên server)

| Đặc điểm | Mô phỏng | Vì sao quan trọng |
|---|---|---|
| Chu kỳ gửi | Giá trị đo: mỗi 10 s khi xe bật; cờ: khi đổi trạng thái + định kỳ | Cần kiểm lại với dữ liệu thật (câu hỏi 1 của plan) |
| Khi đỗ | Xe "ngủ": gửi thưa (ví dụ 30 phút / lần) hoặc không gửi; thức dậy khi sạc / bật từ xa | Bài A cần phiên sạc đầy đủ; kiểm tra cảm biến lúc xe nguội cần mẫu khi đỗ |
| Mất gói | 1–3% mẫu ngẫu nhiên; mất cả đoạn 5–60 phút khi ở hầm, vùng sóng yếu | Thuật toán phải chịu được dữ liệu thiếu |
| Lệch giờ, trùng | Thỉnh thoảng trùng mẫu, timestamp lệch vài giây | Kiểm tra bước làm sạch dữ liệu |
| Cột không áp dụng | Để trống (lệnh từ app khi không có lệnh; EDS sau trên xe 1 motor) | Giống dữ liệu thật |

---

## 6. Lỗi: tác động vào đâu, phát triển thế nào

**Cách chung:**
- Mỗi lỗi có `onset` (ngày bắt đầu), `kiểu tiến triển` (đột ngột / tuyến tính / tăng tốc dần) và `severity(t)` từ 0 tới 1.
- Lỗi chỉ đổi **tham số bộ phận**.
- Khoảng **15–25% số xe** có ít nhất một lỗi trong 180 ngày; khoảng 3% có hai lỗi cùng lúc.
- Các xe còn lại khỏe, dùng để kiểm tra báo nhầm.

| Lỗi | Tham số bị đổi | Tiến triển | Có cờ không | Bài |
|---|---|---|---|---|
| **Két nước / dàn nóng bẩn** | `độ_sạch_két` 1 → 0,4 | Tuyến tính 3–6 tháng (nhanh hơn ở xe chạy đường bụi) | Không | **B** (chính), A (dàn nóng) |
| **Quạt két chết** | Quạt = 0 dù có lệnh | Đột ngột | Có (`34233.2.9`) khi có lệnh quạt | B, A |
| **Bơm motor mòn** | Lưu lượng motor 1 → 0,4 | Tăng tốc dần | Chỉ khi hỏng hẳn (`34233.2.192`) | **B** |
| **Rò nước làm mát** | Mức nước giảm 0,5–5% / ngày | Tuyến tính | Có khi < ngưỡng (`34200.7.1`) | A, B, bài 1 |
| **Rò gas chậm** | Lượng gas 100 → 50% | Tuyến tính 1–5% / tháng | Chỉ khi gần hết | **A**, bài 3, B7 |
| **Chiller đóng cặn** | `hiệu_suất_chiller` 1 → 0,2 | Tuyến tính | Không | **A** |
| **Bơm pin yếu** | Lưu lượng pin 1 → 0,3 | Tăng tốc dần | Chỉ khi hỏng hẳn | **A** |
| **Van chia nước kẹt** | Kẹt ở một chế độ | Đột ngột | Có (`34233.2.11`) | A, B |
| **AGS kẹt đóng** | Gió qua két giảm khi xe chậm | Đột ngột | Có (`34200.2.32`) | B, A |
| **PTC gió hỏng** | P_PTC_gió = 0 | Đột ngột | Có (`34233.2.198`) | **C** |
| **PTC nước hỏng** | P_PTC_nước = 0 | Đột ngột | Có (`34233.2.198`) | **A** mùa đông |
| **Cửa gió trộn kẹt phía lạnh** | Cửa trộn = 0 | Đột ngột | **Không** | **C** |
| **Lọc gió tắc** | Độ thông 1 → 0,4 | Tuyến tính theo km | Không | C (yếu) |
| **Cảm biến lệch / đứng / trôi** | Lớp cảm biến (mục 5.1) | Đột ngột / trôi dần | Đôi khi | Bước lọc cảm biến |

**Ví dụ chuỗi hệ quả (két bẩn dần, bài B):**
```
độ_sạch_két giảm → Q_két giảm → nước motor nóng hơn vài độ → motor / EDS nóng hơn ở cùng tải
→ (tuần đầu) chỉ thấy qua phần chênh so với kỳ vọng (M1)
→ (vài tháng sau) leo đèo trời nóng thì motor > 130°C → đèn giới hạn công suất bật
→ đồng thời dàn nóng cũng bẩn → điều hòa kém khi xe chậm, sạc nhanh giữa trưa bị chậm hơn
```

---

## 7. Nhãn đúng cho từng bài

Ngoài bảng lỗi (`fault_type`, `onset`, `severity(t)`), mỗi bài cần nhãn ở đơn vị phân tích của nó. **Dùng phép "nếu như"**: với mỗi phiên / sự kiện, chạy lại đúng đoạn đó với tham số **xe khỏe** (hoặc bỏ giới hạn nhiệt) và so sánh.

### Bài A: mỗi phiên sạc DC

| Nhãn | Cách tạo |
|---|---|
| `minutes_lost_true` | Chạy lại phiên với **dòng cho phép không bị giới hạn do nhiệt**; thời gian chênh tới cùng SOC = số phút mất do nhiệt |
| `minutes_lost_fault` | Chạy lại với **hệ làm mát khỏe** (bỏ các lỗi); thời gian chênh = phần do hỏng hóc, phần còn lại do điều kiện |
| `cause_true` | Theo phần lớn phút mất: do pin nóng vì tải / thời tiết, do làm mát kém (kèm lỗi cụ thể), do pin lạnh vì không làm ấm, do làm ấm kém (PTC nước), hay do trạm |
| `thermally_limited_true` | `minutes_lost_true` ≥ 2 phút |

### Bài B: mỗi sự kiện giới hạn công suất, và theo xe × tuần

| Nhãn | Cách tạo |
|---|---|
| `source_true` | Ngưỡng nào bật trước: motor / inverter → `motor_eds`; pin → `pin` |
| `cause_true` | Chạy lại đoạn 30 phút trước sự kiện với **hệ làm mát khỏe**: nếu không còn sự kiện → `he_lam_mat_kem` (kèm lỗi cụ thể); nếu vẫn còn → `moi_truong_nong` / `tai_nang` theo điều kiện |
| `days_to_first_derate` | Với xe có lỗi tiến triển: số ngày từ lúc lỗi bắt đầu tới sự kiện đầu tiên. Dùng để đo **báo sớm được bao nhiêu ngày** |
| `cooling_health_true` | Độ khỏe hệ làm mát motor theo tuần (từ độ sạch két, lưu lượng bơm, mức nước): mục tiêu mà M1 phải theo dõi được |

### Bài C: mỗi chuyến có sưởi

| Nhãn | Cách tạo |
|---|---|
| `time_to_setpoint_true` | Từ nhiệt cabin thật, không nhiễu |
| `heating_status_true` | Chạy lại với **hệ sưởi khỏe**: nếu chậm hơn nhiều → `kem_nong` / `khong_suoi`; nếu cũng chậm như vậy → `binh_thuong` (do trời quá lạnh, gió thấp) |
| `cause_true` | Lỗi đang có: PTC gió / cửa trộn / lọc gió |

---

## 8. Đầu ra

```
du_lieu_gia/
  telemetry/vin=VF_SIM_0001/date=2026-11-01.parquet   ← chỉ các cột có trong từ điển (299 + thời gian), đã qua lớp cảm biến và telemetry
  truth/vin=VF_SIM_0001/date=2026-11-01.parquet       ← trạng thái thật mỗi 10 s (gas, lưu lượng, độ sạch két, nhiệt thật…) — CHỈ để kiểm tra
  labels/faults.csv            ← vin, fault_type, onset, kiểu tiến triển, severity cuối
  labels/charge_sessions.csv   ← bài A: mỗi phiên + nhãn mục 7
  labels/derate_events.csv     ← bài B: mỗi sự kiện + nhãn; labels/cooling_health_weekly.csv
  labels/heating_trips.csv     ← bài C: mỗi chuyến sưởi + nhãn
  fleet.csv                    ← vin, dòng xe, vùng, kiểu người dùng, tham số riêng của xe
  config.yaml                  ← mọi tham số (mục 9) + seed để sinh lại đúng như cũ
```

Kích thước ước lượng: 200 xe × 180 ngày × khoảng 4–8 giờ xe bật / ngày × 6 mẫu / phút. Khoảng 50–100 triệu dòng; Parquet nén còn vài GB. Có thể sinh bản nhỏ (20 xe × 30 ngày) để thử trước.

---

## 9. Tham số và mức khác nhau giữa các xe

Mỗi xe rút ngẫu nhiên quanh giá trị chuẩn (phân phối chuẩn cắt, σ ghi trong bảng). Các giá trị dưới đây khớp engine hiện tại, quy về đơn vị vật lý.

| Nhóm | Tham số | Chuẩn | Khác giữa xe |
|---|---|---|---|
| Xe | Khối lượng; CdA; Crr | 2100–2600 kg; 0,72 m²; 0,011 | ±3% |
| Pin | Khối nhiệt cell | khoảng 3,5×10⁵ J/K | ±10% |
| | Điện trở trong ở 25°C | khoảng 0,06 Ω (cả pack) | ±10%, tăng theo tuổi pin |
| | UA tấm làm mát (bơm 100%) | khoảng 450 W/K | ±15% |
| | Khối nhiệt nước vòng pin | khoảng 7×10⁴ J/K | ±10% |
| | Lệch vị trí từng đầu đo nhiệt | 0 | ±1,5°C (cố định theo xe) |
| Gas | Q lạnh định mức | khoảng 6,5 kW | ±8% |
| | UA chiller | khoảng 260 W/K | ±10% |
| Motor | Khối nhiệt motor / inverter | khoảng 4×10⁴ / 8×10³ J/K | ±10% |
| | UA motor ↔ nước, inverter ↔ nước | khoảng 70 / 60 W/K | ±10% |
| | UA két (gió và lưu lượng tối đa) | khoảng 600 W/K | ±12% |
| Cabin | Khối nhiệt cabin; UA vỏ | khoảng 9×10⁴ J/K; 130 W/K | ±10% |
| | PTC gió; PTC nước | 5 kW; 5 kW | ±5% |
| Cảm biến | Lệch cố định mỗi cảm biến | 0 | ±0,3°C |
| Điều khiển | Các ngưỡng mục 4 | như bảng | ±1°C |

Mức khác nhau giữa các xe là thứ làm **luật cứng có báo nhầm và bỏ sót**, nên ML (học theo từng xe) có chỗ để tốt hơn.

---

## 10. Kiểm tra dữ liệu giả có hợp lý không

| Kiểm tra | Cách làm | Đạt khi |
|---|---|---|
| Năng lượng | Tổng điện vào / ra pin khớp SOC; tiêu thụ trung bình | 15–25 kWh/100 km tùy xe, mùa |
| Đường sạc | Công suất theo SOC ở pin 25°C | Hình dạng giống các đường sạc công khai (Fastned) |
| Pin khi sạc nhanh | Cell tăng bao nhiêu độ trong 30 phút sạc | Tương đồng dữ liệu Tesla của KU Leuven (vài tới hơn chục độ tùy công suất) |
| Cabin khi sưởi | Thời gian cabin từ 10°C lên 22°C | Tương đồng dữ liệu BMW i3 (khoảng 10–20 phút) |
| Cabin khi làm mát | Từ 55°C (đỗ nắng) xuống 25°C | Khoảng 10–20 phút |
| Xe khỏe | Chạy cả đội xe không có lỗi | **Không** có cờ lỗi bộ phận; giới hạn công suất rất hiếm (chỉ khi leo đèo trời rất nóng, chở nặng) |
| Xe có lỗi | Từng lỗi riêng lẻ | Đúng chuỗi hệ quả mục 6; mức độ tăng dần theo `severity` |
| Đủ dữ liệu cho mỗi bài | Đếm phiên sạc DC, sự kiện giới hạn, chuyến sưởi | Đủ để chấm điểm (ví dụ ≥ 5.000 phiên DC, ≥ 200 sự kiện, ≥ 3.000 chuyến sưởi) |

---

## 11. Thứ tự làm

1. **Port engine một xe** từ `vinfast_thermal_3d.html` sang Python, bước 1 giây. So khớp với CSV xuất từ trang web cho cùng kịch bản (sai lệch nhỏ).
2. **Thêm lớp cảm biến và telemetry** (mục 5), xuất đúng cột từ điển (bổ sung 20 tín hiệu mới cho đủ 299).
3. **Sinh lịch trình và thời tiết** (mục 2) → chạy 1 xe × 30 ngày, vẽ biểu đồ kiểm tra (mục 10).
4. **Thêm lỗi tiến triển** (mục 6) và **nhãn "nếu như"** (mục 7).
5. **Sinh cả đội xe** (song song theo xe), kiểm tra mục 10, chốt `config.yaml` + seed.
6. Bàn giao cho bước baseline A → B → C.

Các bước 1–3 có thể kiểm tra trực quan bằng trang 3D: nạp CSV một xe để xem lại trên mô hình (tính năng có thể bổ sung sau).
