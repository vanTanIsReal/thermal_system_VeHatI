# VeHatI – Nhóm Nhiệt & Điều hòa (Thermal & HVAC)

> Kế hoạch tìm hiểu bộ phận, lỗi thường gặp và các bài toán liên quan.
> Ghi chú: các trường trong tài liệu (`ambient_temp`, `evap_temp`…) là **tên gọi nội bộ**. Mục 6 ánh xạ từng tên sang tín hiệu thật trong `resource_dictionary_full.csv` (mã `content.xxxxx`), kèm trạng thái: **có giá trị** / **chỉ có cờ, trạng thái** / **không có**.
> Từ điển chỉ có tên tín hiệu: chưa xác nhận đơn vị, tần suất gửi, dòng xe nào gửi tín hiệu nào, và tín hiệu có dữ liệu thật hay không. Việc xếp loại ✅/🟡/❌ là **suy từ tên**, cần kiểm lại trên một mẫu dữ liệu thật.
> Nguồn của từng phần: **tên / mã tín hiệu và mức khả thi** lấy từ từ điển; **cấu tạo hệ thống, vị trí, lỗi hay gặp, cách làm baseline** là kiến thức kỹ thuật chung, chưa đối chiếu với tài liệu sửa chữa của dòng xe cụ thể.

---

## 1. Tổng quan hệ thống nhiệt trên xe điện

Xe điện có **3 vòng nhiệt + 1 hộp HVAC**, nối với nhau qua **chiller** và **van chia nước 3/4 ngả**:

```
[Vòng gas lạnh]   Máy nén điện (EAC) → Dàn nóng (+quạt két, AGS) → Van tiết lưu EXV ─┬→ Dàn lạnh (làm mát cabin)
                                                                                      └→ CHILLER (làm mát nước của pin)
[Vòng nước pin]   Bơm pin → Chiller / PTC sưởi nước → Tấm làm mát dưới pin → Bình nước phụ
[Vòng nước motor] Bơm motor → OBC / DC-DC → Inverter → Motor trước (+ EDS sau trên xe 2 motor) → Két nước (+quạt)
                  (van 3/4 ngả có thể nối sang vòng pin)
[HVAC cabin]      Blower + lọc gió + dàn lạnh + sưởi PTC/heat pump + cửa gió trộn 2 vùng (tài xế/hành khách) + cảm biến cabin
```

- **Chiller**: bộ trao đổi nhiệt giữa gas lạnh và nước làm mát. Đây là "cầu nối" để điều hòa làm mát pin.
- **Heat pump** (nếu có): đảo chiều vòng gas để sưởi. Dòng xe không có heat pump thì dùng PTC (điện trở sưởi). Từ điển tín hiệu **không có trường nào về heat pump**, khớp với giả định dùng PTC, nhưng chưa đủ để kết luận.
- **AGS** (lưới tản nhiệt chủ động): từ điển có tín hiệu lỗi riêng (`VCU Ags component error level`) → nhiều khả năng có trên ít nhất một dòng xe. Đóng/mở để giảm cản gió hoặc cấp gió cho dàn nóng/két nước.
- **Xe 2 motor**: từ điển có đủ bộ cờ cho **EDS FR** và **EDS RR** → có thể có dòng 2 motor, khi đó cụm EDS sau cũng nằm trên vòng nước motor. Từ điển có thể là danh sách chung cho mọi dòng xe, nên **cần xác nhận** đội xe của team có dòng nào.
- **Điều hòa 2 vùng**: từ điển có nhiệt cài đặt riêng cho tài xế và hành khách (`Driver/Passenger Temperature`) → có thể có trên một số dòng xe (cần xác nhận).

---

## 2. Bộ phận: vị trí, lỗi thường gặp, dấu hiệu trên telemetry

Cột cuối ghi tín hiệu **có thật** trong từ điển. Dấu hiệu nào cần tín hiệu không có thì đã ghi rõ.

| Bộ phận | Nằm ở đâu | Hay hỏng gì | Thấy được trên telemetry qua (tín hiệu thật) |
|---|---|---|---|
| Máy nén điện (EAC) | Khoang trước | Kẹt, hỏng mạch biến tần, mất cách điện, thiếu dầu | Chỉ có cờ: `EAC Compressor Fault Status`, `VCU Hvac component error level`. **Không có** tốc độ, lệnh tốc độ, công suất máy nén → chỉ suy gián tiếp qua nhiệt dàn lạnh / nhiệt cabin |
| Dàn nóng + quạt két | Đầu xe, sau cản | Bám bẩn, móp, quạt chết/yếu | Chỉ có `VCU Fan component error level`. **Không có** áp suất cao, duty / tốc độ quạt |
| Lưới tản nhiệt chủ động (AGS) | Cản trước | Kẹt đóng / kẹt mở, mô-tơ hỏng | Chỉ có `VCU Ags component error level`. Không có vị trí lá chắn |
| Van tiết lưu EXV | Gần vách ngăn khoang máy | Kẹt, mở sai độ | `VCU Valve component error level`; nhiệt dàn lạnh bất thường. **Không có** lệnh/vị trí EXV, áp suất thấp → không tính được superheat |
| Dàn lạnh | Hộp HVAC sau taplo | Đóng băng, bẩn, rò | `Actual evaporator temperature` < 0°C kéo dài, hoặc AC bật mà nhiệt dàn lạnh không xuống; `Interior temperature` không về nhiệt cài đặt. **Không có** nhiệt gió ra cửa gió |
| Chiller | Khoang trước | Rò, đóng cặn, van chiller kẹt | BMS yêu cầu công suất làm mát (`requesting the cooling power required for the battery pack`) mà chênh nhiệt nước vào/ra pin nhỏ. **Không có** `chiller_status` |
| Bơm nước (pin / motor) | Khoang trước, phía dưới | Mòn, kẹt, lỗi điện, có khí trong hệ | Chỉ có trạng thái bơm (`Battery / Motor electronic pump state`) và cờ `Water pump failure`. **Không có** tốc độ bơm |
| Két nước | Đầu xe | Tắc, rò | Nhiệt motor / EDS cao dù tải bình thường; cờ `Cooling water temperature is too high` (EDS FR / RR). **Không có** nhiệt nước vào/ra vòng motor |
| Ống & kẹp ống | Khắp khoang trước, chạy xuống pin | Lão hóa, nứt, kẹp lỏng → rò | Cảnh báo `Low level coolant water`, `Coolant Leakage warning` |
| Bình nước phụ + cảm biến mức | Khoang trước | Nứt, cảm biến mức kẹt | Chỉ có cảnh báo thiếu nước / rò. **Không có** giá trị mức nước |
| Van 3/4 ngả | Khoang trước | Kẹt ở một vị trí | Chỉ có `VCU Valve component error level`. **Không có** lệnh/vị trí van |
| PTC / heat pump | Hộp HVAC / vòng nước | Không sưởi, sưởi yếu | Cờ `PTC module failure`, `VCU Ptc component error level` (chưa rõ PTC gió hay PTC nước); `Battery pack precondition information`. **Không có** công suất PTC, nhiệt gió ra |
| Blower, lọc gió, cửa gió | Sau taplo | Lọc tắc, blower yếu, cửa gió kẹt | Chỉ có mức gió đã chọn (`Air Blow Level`), hướng gió (`Air Flow`). **Không có** công suất / tốc độ blower, vị trí flap thực |
| OBC / DC-DC / inverter / motor | Khoang trước (+ trục sau trên xe 2 motor) | Quá nhiệt → giảm công suất | `Motor Temperature`, `EDS current temperature`; cờ quá nhiệt motor / IGBT / tấm dẫn động (drive plate) / OBC / DC-DC; `Power limitation warning`, `VCU Electric Motor power reduced` |
| Cảm biến nhiệt / áp suất | Khắp nơi | Trôi, đứng giá trị, mất tín hiệu | Lệch so với cảm biến khác khi xe để nguội lâu (`Parking duration`); cờ `VCU Tsen component error level`, `External Temperature Fail Sts`, `EDS temp offset checkout alarm`, cờ lỗi cảm biến nhiệt của BMS / EDS |

---

## 3. Bốn bài toán đã có và phần còn trống

| # | Bài đã có | Bộ phận chính | Khả thi với telemetry hiện có |
|---|---|---|---|
| 1 | Phát hiện rò/thiếu nước làm mát, bất thường vòng làm mát | Ống, kẹp, bình nước phụ, bơm, két | ✅ Làm được (cảnh báo thiếu nước / rò, nhiệt nước vào/ra pin, cờ bơm) |
| 2 | Phát hiện sớm lỗi điều hòa theo dòng xe và mùa | Toàn đội xe (fleet) | 🟡 Một phần (dựa trên cờ lỗi + nhiệt dàn lạnh / cabin) |
| 3 | Điều hòa kém lạnh nhận ra từ telemetry | Vòng gas lạnh + cabin | 🟡 Một phần (nhiệt dàn lạnh, nhiệt cabin so với cài đặt; không có áp suất, tốc độ máy nén) |
| 4 | Phân biệt kiểu hỏng: không đủ lạnh / không hoạt động / máy nén / quạt / chiller | Vòng gas lạnh | 🟡 Một phần (phân biệt chủ yếu qua cờ lỗi từng bộ phận) |

**Còn trống:** chất lượng cảm biến, sức khỏe làm mát pin, rò gas chậm (dự báo trước), giảm công suất do nhiệt, sạc nhanh chậm vì nhiệt, sưởi, van/cửa gió kẹt, lọc gió/blower, năng lượng HVAC, độ tin cậy linh kiện / bảo hành.

---

## 4. Bài toán mới đề xuất

Mẫu chung cho mỗi bài: **Phát biểu → Loại → Input → Output → Cách làm baseline → Đánh giá → Phần trùng với bài khác.**

### ✅ Bài toán chốt (10/2026)

Tiêu chí: lỗi **khách hàng dễ gặp và tự thấy rõ** (đồng hồ báo, xe yếu, sạc lâu, cabin không ấm), **telemetry đủ tín hiệu** để làm, và **đầu ra đo được** (số phút, số lần, nguyên nhân). Các bài 1–4 đã có (rò nước, điều hòa kém lạnh…) không lặp lại ở đây.

| # | Bài | Khách hàng gặp gì | Mức dễ gặp |
|---|---|---|---|
| A | **Sạc nhanh bị chậm vì nhiệt** (B9) | Cắm sạc nhanh mà lâu hơn bình thường nhiều; app báo thời gian sạc dài | Rất dễ gặp: trưa nắng sau khi chạy (pin nóng), sáng đông miền Bắc (pin lạnh) |
| B | **Xe bị giảm công suất vì quá nhiệt** (B8) | Xe đột nhiên yếu, tăng tốc kém; đồng hồ hiện đèn báo giới hạn công suất | Gặp khi leo đèo, chạy cao tốc lâu, trời nóng, chở nặng |
| C | **Sưởi kém / không sưởi** (B10) | Bật sưởi mà cabin vẫn lạnh, kính mờ lâu | Mùa đông miền Bắc (tháng 12–3) |

Bước chung cho cả ba bài: lọc cảm biến nhiệt sai trước khi kết luận (so các cảm biến với nhau lúc xe đỗ nguội ≥ 6 giờ, lệch > 3°C thì loại số đo đó).

#### A. Sạc nhanh bị chậm vì nhiệt
- **Câu hỏi:** phiên sạc này mất bao nhiêu phút vì nhiệt, và do pin nóng hay pin lạnh?
- **Đơn vị phân tích:** mỗi phiên sạc nhanh DC.
- **Tín hiệu:** công suất sạc `34220.1.118` · dòng sạc cho phép `34220.1.106` · SOC `34183.1.9` · nhiệt cell lớn nhất / nhỏ nhất `34220.1.80 / .78` · BMS yêu cầu làm mát `34220.1.109` · nước vào / ra pin `34220.1.104 / .105` · làm ấm pin `34233.4.4` · đang sạc, loại sạc `34193.1.5 / .32` · nhiệt ngoài trời `34183.1.7`.
- **Cách làm (baseline luật):**
  1. Đường sạc chuẩn công suất theo SOC cho từng dòng xe: lấy từ spec, hoặc phân vị 90 các phiên sạc có nhiệt pin 20–35°C.
  2. Phiên bị giới hạn do nhiệt: công suất thực / chuẩn < 0,85 kéo dài ≥ 2 phút **và** nhiệt pin ngoài vùng tối ưu (cell lớn nhất > 45°C hoặc cell nhỏ nhất < 15°C). Nhiệt pin bình thường mà công suất vẫn thấp → **không do nhiệt** (nghi trạm sạc yếu).
  3. `minutes_lost` = thời gian sạc thực − thời gian theo đường chuẩn cho cùng khoảng SOC.
  4. Nguyên nhân:
     - Pin nóng + nước vào pin thấp hơn cell ≥ 7°C → làm mát chạy tốt, do tải nhiệt cao (chạy nhiều trước khi sạc, trời nóng).
     - Pin nóng + nước vào pin chỉ thấp hơn cell < 6°C → **làm mát pin kém** (nghi chiller / thiếu gas / quạt két); nước ra – vào pin chênh > 4,5°C → nghi bơm yếu, thiếu nước.
     - Pin lạnh + đã làm ấm trước → **làm ấm kém** (nghi PTC nước).
     - Pin lạnh + không làm ấm trước → do cách dùng (không bật làm ấm / không dẫn đường tới trạm).
- **Đầu ra:**
  ```json
  {"session_id": "S-88812", "vin": "VF000123", "thermally_limited": true, "minutes_lost": 11,
   "cause": "lam_mat_pin_kem", "suspected_part": "chiller"}
  ```
  `cause ∈ {tai_nhiet_cao, lam_mat_pin_kem, lam_am_kem, khong_lam_am_truoc, khong_do_nhiet}`
- **Đánh giá:** cờ `Super Fast Charge Longer` (`34193.1.30`) và `Pack Power Degrade: battery is cold` (`34220.1.93`) làm nhãn tham khảo; lỗi bơm vào dữ liệu giả (chiller, bơm, gas, quạt, PTC); về sau đối chiếu phiếu sửa chữa ở xưởng.
- **Trên mô phỏng:** bắt được PTC hỏng mùa đông (công suất còn ~60–70% đường chuẩn); nguyên nhân "làm mát pin kém" bắt được chiller còn ≤ 15–20%, bơm 40%, rò gas, quạt chết, van kẹt; không báo nhầm ở xe khỏe.

#### B. Xe bị giảm công suất vì quá nhiệt
- **Câu hỏi:** xe nào hay bị giới hạn công suất vì nóng, ở motor/EDS hay ở pin, và do điều kiện chạy hay do hệ làm mát kém?
- **Đơn vị phân tích:** mỗi sự kiện giới hạn công suất; tổng hợp theo xe × tháng.
- **Tín hiệu:** đèn báo giới hạn công suất `34200.1.68 / 34200.25.28`, `34200.9.5`, giảm công suất motor `34200.9.6` · BMS yêu cầu chế độ giới hạn `34220.1.70` · nhiệt motor / EDS `34233.3.231 / .232` · cờ quá nhiệt IGBT, drive plate, nước làm mát EDS `34233.3.57 / .58 / .88 / .89 / .56 / .87 / .10 / .34` · mô-men thực `34233.3.148 / .153` · tốc độ `34183.1.2` · bàn đạp ga `34183.1.26` · nhiệt cell lớn nhất `34220.1.80` · dòng xả cho phép `34220.1.107` · nhiệt ngoài trời `34183.1.7` · odometer `34183.1.3` · cờ quạt két, thiếu nước `34233.2.9`, `34200.7.1`.
- **Cách làm (baseline luật):**
  1. Sự kiện = đèn báo giới hạn công suất bật; ghép các lần bật cách nhau < 2 phút thành một sự kiện.
  2. Nguồn: cờ quá nhiệt EDS / IGBT / nước làm mát EDS → **motor / EDS**; cell lớn nhất > 50°C hoặc BMS yêu cầu chế độ giới hạn / dòng xả cho phép giảm → **pin**.
  3. Nguyên nhân: nhiệt ngoài trời > 38°C → **môi trường nóng**; mô-men hoặc bàn đạp ga > phân vị 90 trong 5 phút trước sự kiện → **tải nặng**; còn lại → **hệ làm mát kém** (kèm gợi ý nếu có cờ quạt két / thiếu nước).
  4. Xếp hạng xe theo số sự kiện / 1000 km so với xe cùng dòng.
- **Đầu ra:**
  ```json
  {"vin": "VF000123", "month": "2026-10", "derate_events_per_1000km": 4.2, "derate_minutes_total": 37,
   "source": "motor_eds", "main_cause": "he_lam_mat_kem", "fleet_percentile": 97}
  ```
  `source ∈ {motor_eds, pin}` · `main_cause ∈ {moi_truong_nong, tai_nang, he_lam_mat_kem}`
- **Đánh giá:** đèn báo chính là nhãn sự kiện; nguyên nhân đánh giá bằng lỗi bơm vào dữ liệu giả (rò nước, quạt chết, van kẹt) và phiếu sửa chữa ở xưởng.
- **Lưu ý:** sự kiện hiếm trên một xe → cần gộp toàn đội xe nhiều tháng mới đủ số liệu.

#### C. Sưởi kém / không sưởi
- **Câu hỏi:** xe nào bật sưởi mà cabin không ấm lên được, và nghi bộ phận nào?
- **Đơn vị phân tích:** mỗi chuyến đi có bật sưởi ≥ 10 phút.
- **Tín hiệu:** chế độ điều hòa `34184.1.5` · nhiệt cabin `34183.1.15` · nhiệt cài đặt `34184.1.6` · nhiệt ngoài trời `34183.1.7` · mức gió `34184.1.25` · sấy kính trước `34184.1.9` · cờ lỗi PTC `34233.2.198 / 34233.2.10` · lỗi điều hòa `34200.11.2`.
- **Cách làm (baseline luật):**
  1. Thời gian để cabin tới gần nhiệt cài đặt (`time_to_setpoint`), chuẩn hóa theo nhiệt ngoài trời và mức gió; so với xe cùng dòng, cùng ngày, cùng vùng.
  2. Sau 10 phút sưởi mà cabin vẫn thấp hơn cài đặt > 5°C → **sưởi kém**.
  3. Nguyên nhân: có cờ lỗi PTC → **PTC hỏng**; không có cờ → nghi PTC yếu / cửa gió trộn kẹt / blower yếu.
- **Đầu ra:**
  ```json
  {"vin": "VF000123", "date": "2026-01-10", "heating_status": "kem_nong",
   "time_to_setpoint_min": null, "suspected_cause": "ptc"}
  ```
  `heating_status ∈ {binh_thuong, cham, kem_nong, khong_suoi}` · `suspected_cause ∈ {ptc, cua_gio_tron, blower, chua_ro}`
- **Đánh giá:** cờ lỗi PTC làm nhãn tham khảo; lỗi bơm vào dữ liệu giả (PTC hỏng); phiếu sửa chữa mùa đông.
- **Lưu ý:** chủ yếu có dữ liệu ở miền Bắc mùa đông; xe có heat pump sưởi khác PTC (cần biết dòng xe nào có heat pump).
- **Trên mô phỏng:** PTC hỏng → cabin thấp hơn cài đặt ~12°C sau 10 phút, phát hiện đúng, kèm sạc nhanh sau đó bị chậm vì pin lạnh (bài A).

> Ngưỡng (0,85; 45°C; 15°C; 7°C; 6°C; 4,5°C; 38°C; 5°C) chọn từ dữ liệu mô phỏng chưa hiệu chuẩn theo xe VinFast → **phải chỉnh lại trên mẫu dữ liệu thật** trước khi dùng.

### Phân tích 3 bài chốt: input – output – hành động – linh kiện – bài liên quan

#### A. Sạc nhanh bị chậm vì nhiệt

| Mục | Nội dung |
|---|---|
| **Input** | **Sạc:** công suất sạc, dòng sạc cho phép, SOC, đang sạc / loại sạc · **Nhiệt pin:** cell lớn nhất / nhỏ nhất, chênh nhiệt cell · **Làm mát / làm ấm pin:** BMS yêu cầu làm mát, nước vào / ra pin, trạng thái bơm pin, thông tin làm ấm pin · **Môi trường:** nhiệt ngoài trời · **Nhãn tham khảo:** `Super Fast Charge Longer`, `Pack Power Degrade: battery is cold` |
| **Output** | Mỗi phiên sạc: có bị giới hạn do nhiệt không, **số phút mất**, nguyên nhân (`tai_nhiet_cao` / `lam_mat_pin_kem` / `lam_am_kem` / `khong_lam_am_truoc` / `khong_do_nhiet`), bộ phận nghi ngờ. Tổng hợp theo xe × tháng: số phiên bị chậm, tổng phút mất |
| **Hành động** | **Khách hàng / app:** giải thích vì sao sạc chậm; nhắc bật làm ấm pin hoặc dẫn đường tới trạm trước khi sạc mùa đông · **Xưởng dịch vụ:** `lam_mat_pin_kem` lặp lại ≥ 3 phiên → hẹn kiểm tra chiller + van chiller, lượng gas, quạt két, bơm pin, mức nước; `lam_am_kem` → kiểm tra PTC nước · **Kỹ thuật (R&D):** phân bố phút mất theo dòng xe và khí hậu → chỉnh ngưỡng bật làm mát / làm ấm, chiến lược làm ấm trước khi sạc · **Chất lượng:** tỉ lệ xe làm mát kém theo lô chiller / bơm |
| **Linh kiện liên quan** | **Trực tiếp:** pin (cell, tấm làm mát, BMS, cảm biến nhiệt cell và nước vào / ra) · **Làm mát pin:** chiller, van chiller, máy nén, gas lạnh, dàn nóng, quạt két, bơm nước pin, van chia nước, bình nước phụ · **Làm ấm pin:** PTC nước · **Loại trừ:** cổng sạc, contactor sạc nhanh, BDU, trạm sạc (ngoài xe) |
| **Bài liên quan** | Bài 1 rò nước (thiếu nước → lưu lượng giảm) · bài 3 · 4 vòng gas (thiếu gas, quạt két làm chiller yếu) · B6 sức khỏe làm mát pin (xu hướng theo tuần) · B12 van chiller / van chia nước kẹt · **C** (PTC nước hỏng → pin lạnh → sạc chậm) · B5 lọc cảm biến · B14 độ tin cậy chiller / bơm |

#### B. Xe bị giảm công suất vì quá nhiệt

| Mục | Nội dung |
|---|---|
| **Input** | **Sự kiện:** đèn báo giới hạn công suất, giảm công suất motor / hệ cao áp, BMS yêu cầu chế độ giới hạn · **Nhiệt:** motor, EDS, cờ quá nhiệt IGBT / drive plate / nước làm mát EDS (trước, sau), cell lớn nhất · **Tải:** mô-men thực motor trước / sau, tốc độ, bàn đạp ga, dòng xả cho phép · **Môi trường:** nhiệt ngoài trời · **Hệ làm mát:** cờ quạt két, cờ thiếu nước, trạng thái bơm motor · **Chuẩn hóa:** odometer, dòng xe |
| **Output** | Mỗi sự kiện: thời lượng, **nguồn** (`motor_eds` / `pin`), **nguyên nhân** (`moi_truong_nong` / `tai_nang` / `he_lam_mat_kem`). Theo xe × tháng: số sự kiện / 1000 km, tổng phút, phân vị so với xe cùng dòng |
| **Hành động** | **Khách hàng / app:** giải thích “xe giới hạn công suất để bảo vệ motor / pin”, gợi ý (giảm tải, nghỉ khi leo đèo dài) · **Xưởng dịch vụ:** `he_lam_mat_kem` lặp lại hoặc xe ở phân vị > 95 → kiểm tra két nước (tắc), quạt két, bơm motor, mức nước, van chia nước, AGS; nguồn `pin` → kiểm tra hệ làm mát pin (như bài A) · **Kỹ thuật (R&D):** xem ngưỡng giới hạn và chiến lược quạt / bơm theo tuyến đường (đèo, cao tốc) · **Chất lượng:** tỉ lệ sự kiện theo lô motor / inverter / két nước |
| **Linh kiện liên quan** | **Trực tiếp:** motor trước / sau, inverter / EDS (IGBT, cảm biến nhiệt stator) · **Làm mát motor:** bơm nước motor, két nước, quạt két, AGS, van chia nước, bình nước phụ, ống & kẹp · **Cùng vòng nước:** OBC, DC-DC · **Khi nguồn là pin:** pin, BMS, toàn bộ hệ làm mát pin |
| **Bài liên quan** | Bài 1 rò nước (thiếu nước → motor nóng) · bài 4 quạt két · B12 van kẹt (nước đi tắt bỏ qua két) · AGS kẹt đóng · **A** (khi nguồn là pin nóng) · B5 (cảm biến nhiệt motor lỗi → giới hạn “giả”) · B14 độ tin cậy motor / inverter |

#### C. Sưởi kém / không sưởi

| Mục | Nội dung |
|---|---|
| **Input** | **Điều hòa:** chế độ (sưởi / lạnh), nhiệt cài đặt, mức gió, sấy kính trước / sau, gió hồi · **Kết quả:** nhiệt cabin · **Môi trường:** nhiệt ngoài trời · **Cờ lỗi:** PTC module failure, mức lỗi PTC (VCU), lỗi điều hòa · **Ngữ cảnh:** dòng xe (PTC hay heat pump), vùng, mùa |
| **Output** | Mỗi chuyến có sưởi: **thời gian cabin đạt nhiệt cài đặt**, trạng thái (`binh_thuong` / `cham` / `kem_nong` / `khong_suoi`), nguyên nhân nghi ngờ (`ptc` / `cua_gio_tron` / `blower` / `chua_ro`). Theo xe × mùa: tỉ lệ chuyến sưởi kém |
| **Hành động** | **Khách hàng / app:** gợi ý bật sưởi trước qua app / lịch điều hòa; cảnh báo khi PTC có lỗi · **Xưởng dịch vụ:** có cờ PTC → thay / sửa PTC; không có cờ → kiểm tra cửa gió trộn, blower, lọc gió, cảm biến nhiệt cabin · **Kỹ thuật (R&D):** so sánh dòng PTC với dòng heat pump; điện năng sưởi ảnh hưởng quãng đường mùa đông · **Chất lượng:** tỉ lệ hỏng PTC theo lô |
| **Linh kiện liên quan** | **Trực tiếp:** PTC gió (hoặc PTC nước + két sưởi), heat pump (dòng có) · **Đưa nhiệt vào cabin:** blower, lọc gió, cửa gió trộn, cửa gió hồi / hướng gió, cửa sấy kính · **Đo & điều khiển:** cảm biến nhiệt cabin, CCU · **Liên quan:** PTC nước của pin, sấy kính sau |
| **Bài liên quan** | **A** (PTC nước hỏng → pin lạnh → sạc nhanh chậm mùa đông) · B12 cửa gió trộn kẹt · B13 lọc gió tắc / blower yếu · B11 năng lượng sưởi → quãng đường mùa đông · B5 cảm biến nhiệt cabin lệch |

#### Ma trận linh kiện × bài chốt

| Linh kiện | A. Sạc chậm vì nhiệt | B. Giảm công suất | C. Sưởi kém |
|---|---|---|---|
| Pin, BMS, cảm biến nhiệt pin | ●● | ● (khi nguồn là pin) | |
| Chiller, van chiller | ●● | ● (nguồn pin) | |
| Máy nén, gas lạnh | ● | | ● (dòng heat pump) |
| Dàn nóng, quạt két, AGS | ● | ●● | |
| Bơm nước pin | ●● | | |
| Bơm nước motor, két nước | | ●● | |
| Van chia nước, bình nước phụ, ống & kẹp | ● | ● | |
| Motor, inverter / EDS | | ●● | |
| OBC, DC-DC | ○ (loại trừ) | ● | |
| PTC nước | ●● | | ● |
| PTC gió / heat pump | | | ●● |
| Blower, lọc gió, cửa gió, cảm biến cabin, CCU | | | ●● |
| Cổng sạc, contactor, BDU | ○ (loại trừ) | | |

●● nguyên nhân chính · ● có ảnh hưởng · ○ cần loại trừ khi kết luận

**Mức khả thi với `resource_dictionary_full.csv`:**

| Bài | Khả thi | Lý do chính |
|---|---|---|
| B5 Cảm biến | 🟡 Một phần | Đủ nhiệt độ; không có áp suất gas → bỏ phần kiểm tra áp suất bão hòa |
| B6 Làm mát pin | ✅ Làm được | Có cell temp, nước vào/ra pin, yêu cầu làm mát của BMS, công suất sạc |
| B7 Rò gas chậm | 🔴 Thiếu tín hiệu | Không có áp suất gas, tốc độ / công suất máy nén |
| B8 Derate | ✅ Làm được | Có nhiệt motor / EDS, cờ quá nhiệt, cảnh báo giới hạn công suất |
| B9 Sạc nhanh chậm vì nhiệt | ✅ Làm được | Có công suất sạc, dòng sạc cho phép, cell temp, precondition, `Super Fast Charge Longer` |
| B10 Sưởi kém | 🟡 Một phần | Không có công suất PTC, nhiệt gió ra; dùng nhiệt cabin so với cài đặt + cờ PTC |
| B11 Năng lượng HVAC | 🟡 Một phần | Chỉ có năng lượng điều hòa **cộng dồn**, không có công suất tức thời |
| B12 Van / cửa gió kẹt | 🔴 Thiếu tín hiệu | Không có phản hồi vị trí; chỉ có cờ lỗi bộ phận |
| B13 Lọc gió / blower | 🔴 Thiếu tín hiệu | Không có công suất / tốc độ blower |
| B14 Độ tin cậy | ⚪ Cần dữ liệu ngoài | Cần claim bảo hành, lô sản xuất |
| B15 Điểm tổng hợp | ✅ Làm được | Gom output các bài khác |

### 🔴 Ưu tiên 1

#### B5. Kiểm tra cảm biến nhiệt/áp suất có đáng tin không
- **Loại:** Luật + thống kê (không cần ML)
- **Khả thi:** 🟡 Một phần. Làm được cho các cảm biến nhiệt; **không có áp suất gas** nên bỏ phần so với áp suất bão hòa.
- **Phát biểu:** Sau khi xe để nguội lâu (đỗ > 6 giờ), mọi cảm biến nhiệt phải ≈ nhiệt môi trường. Cảm biến nào lệch, đứng giá trị hoặc nhiễu thì báo lỗi. **Nên làm đầu tiên**, vì mọi bài khác đều dựa vào cảm biến.
- **Input:** `ambient_temp`, `cabin_temp`, `evap_temp`, `coolant_temp_batt_in/out`, `bms_min/max_cell_temp`, `pack_temp`, `motor_temp`, `eds_temp`, `vehicle_state`, `parked_duration`; cờ lỗi cảm biến có sẵn (`VCU Tsen component error level`, `External Temperature Fail Sts`, `EDS FR/RR temp offset checkout alarm`, cờ cảm biến nhiệt của BMS và stator EDS) dùng làm nhãn đối chiếu.
- **Output:**
  ```json
  {"vin": "VF000123", "sensor_id": "coolant_temp_batt_in", "fault_type": "offset",
   "offset_value": 6.2, "severity": "medium", "first_seen": "2026-09-14"}
  ```
  `fault_type ∈ {stuck, drift, offset, out_of_range, noisy, missing}`
- **Baseline:**
  - Cold-soak check: |T_sensor − T_median_các_cảm_biến| > 3°C → offset.
  - Stuck: phương sai ≈ 0 trong N giờ lúc xe đang chạy.
  - Drift: hồi quy độ lệch theo thời gian, slope > ngưỡng.
- **Đánh giá:** precision/recall trên lỗi cảm biến được bơm vào dữ liệu giả; đối chiếu thêm với các cờ lỗi cảm biến có sẵn.

#### B6. Chỉ số sức khỏe hệ làm mát pin (BTMS Health Index)
- **Loại:** Thống kê
- **Khả thi:** ✅ Làm được. Không có `chiller_status`; dùng `batt_cooling_request` (BMS yêu cầu công suất làm mát) thay thế. Bơm chỉ có trạng thái, không có tốc độ.
- **Phát biểu:** Trong các phiên sạc nhanh DC hoặc chạy tải cao, đo tốc độ hạ nhiệt pin khi BMS đang yêu cầu làm mát, chuẩn hóa theo công suất và nhiệt môi trường. So với baseline của chính xe đó và với các xe cùng dòng.
- **Input:** `bms_max/min_cell_temp`, `cell_temp_delta`, `coolant_temp_batt_in/out`, `batt_cooling_request`, `batt_pump_state`, `charge_power`, `ambient_temp`
- **Output (theo xe, theo tuần):**
  ```json
  {"vin": "VF000123", "week": "2026-W40", "cooling_effectiveness": 0.042,
   "cell_temp_spread_p95": 6.8, "trend_slope_pct_per_month": -4.5,
   "degraded": true, "suspected_cause": "pump"}
  ```
  `suspected_cause ∈ {pump, chiller, low_coolant, unknown}`
- **Baseline:**
  - Hiệu quả làm mát = (dT_pin/dt) / (công suất nhiệt − khả năng tản), làm phẳng theo tuần.
  - So với baseline 30 ngày đầu; giảm > 20% → `degraded`.
  - Chênh nhiệt giữa các cell > 8°C → cờ riêng (đối chiếu `Delta temperature warning signal`).
- **Trùng:** bài 1 (thiếu nước) là một nguyên nhân; B6 đo *hệ quả lên pin*.

#### B7. Rò gas lạnh chậm, ước lượng lượng gas còn lại
- **Loại:** Thống kê (xu hướng)
- **Khả thi:** 🔴 Thiếu tín hiệu. Từ điển **không có** áp suất gas, tốc độ hay công suất máy nén, nên cả (a) và (b) bên dưới đều chưa làm được.
- **Phát biểu gốc:** Bài 3 bắt triệu chứng khi xe *đã* kém lạnh. B7 cố bắt *sớm hơn*, dựa trên:
  - (a) áp suất tĩnh khi để nguội so với áp suất bão hòa của gas tại nhiệt môi trường;
  - (b) xu hướng tăng của tốc độ máy nén cần để đạt nhiệt cài đặt, và xu hướng superheat.
- **Phương án thay thế (yếu hơn):** theo dõi xu hướng "khả năng làm lạnh" theo thời gian:
  - nhiệt dàn lạnh đạt được khi AC chạy, so theo `ambient_temp`;
  - thời gian để `cabin_temp` về `cabin_setpoint` sau khi bật AC (pull-down time);
  - năng lượng điều hòa cộng dồn trên mỗi chuyến, so theo nhiệt môi trường.

  Xu hướng xấu dần → nghi thiếu gas, **nhưng không phân biệt được với dàn nóng bẩn hay quạt yếu**.
- **Input (thay thế):** `evap_temp`, `cabin_temp`, `cabin_setpoint`, `ambient_temp`, `hvac_mode`, `blower_level`, `climate_energy_acc`
- **Output:**
  ```json
  {"vin": "VF000123", "cooling_capacity_trend_pct_per_month": -3.0,
   "status": "nghi_giam_kha_nang_lam_lanh", "confidence": 0.5}
  ```
- **Trùng:** bài 3 (triệu chứng), bài 4 (phân loại). Nếu sau này có áp suất gas / tốc độ máy nén thì quay lại phương án gốc.

#### B8. Giảm công suất do nhiệt (thermal derate) ở motor, inverter và pin
- **Loại:** Thống kê + luật
- **Khả thi:** ✅ Làm được. Không có trường "lý do derate", không có duty quạt → suy nguyên nhân từ các cờ quá nhiệt. **Có mô-men thực** của motor trước / sau (`EDS FR/RR actual output torque of current`) để đo tải, cộng thêm `Accelerator pedal position` và tốc độ.
- **Input:** `motor_temp`, `eds_temp`, `power_limit_flag`, các cờ quá nhiệt (motor, EDS, IGBT, drive plate, nước làm mát quá nóng — FR và RR), `battery_high_temp_warning`, cờ cell quá nóng, `motor_pump_state`, `speed`, `accel_pedal`, `ambient_temp`, `odometer`
- **Output (theo xe):**
  ```json
  {"vin": "VF000123", "derate_events_per_1000km": 4.2, "derate_minutes_total": 37,
   "main_cause": "he_lam_mat_kem", "fleet_percentile": 97}
  ```
  `main_cause ∈ {ambient_cao, tai_nang, he_lam_mat_kem}`
- **Baseline:** luật phân loại nguyên nhân:
  - nhiệt môi trường > 38°C → `ambient_cao`;
  - tải > p90 → `tai_nang`;
  - không thuộc hai trường hợp trên → `he_lam_mat_kem`.

  Sau đó xếp hạng xe theo percentile của số derate trên 1000 km. Cờ quá nhiệt cho biết bộ phận nào (motor / IGBT / pin) gây derate.

#### B9. Sạc nhanh bị chậm vì nhiệt
- **Loại:** Luật (khách hàng thấy rõ)
- **Khả thi:** ✅ Làm được. Không có `charge_power_limit` dạng công suất → dùng dòng sạc cho phép (`Continuous maximum allowable charge current`). Có sẵn cờ `Super Fast Charge Longer` và `Pack Power Degrade: battery is cold` để đối chiếu.
- **Input:** `charge_power`, `c_rate`, `charge_current_allowed`, `charging_type`, `bms_max/min_cell_temp`, `soc`, `batt_cooling_request`, `preconditioning_status`, `fast_charge_longer_flag`, `pack_cold_degrade_flag`, `battery_cold_flags`, `cell_temp_fault_flags`, `ambient_temp`
- **Output (theo phiên sạc):**
  ```json
  {"session_id": "S-88812", "vin": "VF000123", "thermally_limited": true,
   "minutes_lost": 11, "cause": "lam_mat_khong_kip"}
  ```
  `cause ∈ {pin_nong_lam_mat_khong_kip, pin_lanh_khong_preconditioning, lam_mat_khong_dat}`
- **Baseline:** so sánh công suất sạc thực tế với đường sạc chuẩn (công suất theo SOC) của dòng xe; phần thiếu hụt rơi vào lúc nhiệt pin nằm ngoài vùng tối ưu thì tính là do nhiệt. "Làm mát không đạt" = BMS yêu cầu làm mát nhưng chênh nhiệt nước vào/ra pin nhỏ (thay cho `chiller_khong_chay`, vì không có trạng thái chiller).

### 🟡 Ưu tiên 2

#### B10. Sưởi kém / không sưởi (PTC, heat pump, sấy kính)
- **Loại:** Luật + thống kê. Là bài ngược của bài 3, phục vụ mùa đông miền Bắc.
- **Khả thi:** 🟡 Một phần. Không có công suất PTC, nhiệt gió ra, chế độ heat pump. Dựa vào: đang sưởi mà `cabin_temp` không tiến về nhiệt cài đặt, kèm cờ `PTC module failure` / `VCU Ptc component error level` (chưa rõ cờ này là PTC gió hay PTC nước).
- **Input:** `hvac_mode`, `cabin_temp`, `cabin_setpoint`, `ambient_temp`, `blower_level`, `front_defrost`, `ptc_error_flags`
- **Output:**
  ```json
  {"vin": "VF000123", "heating_status": "kem_nong", "suspected_cause": "ptc"}
  ```
  `suspected_cause ∈ {ptc, blower, unknown}`

#### B11. Năng lượng HVAC bất thường
- **Loại:** Hồi quy tuyến tính, sau đó tính residual theo z-score
- **Khả thi:** 🟡 Một phần. Chỉ có `Accumulated Climate Energy Consumption` (cộng dồn) → tính chênh lệch theo chuyến / theo ngày, không có công suất tức thời. Không có `solar_load`.
- **Input:** `climate_energy_acc` (lấy hiệu giữa hai lần đọc), `motor_energy_acc`, `trip_avg_consumption`, `ambient_temp`, `speed`, `cabin_setpoint`, `trip_distance`, `hvac_mode`. Tỉ lệ năng lượng điều hòa / năng lượng motor giúp chuẩn hóa theo cách lái.
- **Output:**
  ```json
  {"vin": "VF000123", "hvac_kwh_per_100km": 3.9, "expected": 2.6,
   "residual_z": 2.8, "flag": true, "range_loss_km": 18}
  ```

#### B12. Van nước / EXV / cửa gió bị kẹt
- **Loại:** Luật. Có thể gộp thành lớp mới cho bài 4.
- **Khả thi:** 🔴 Thiếu tín hiệu. Không có lệnh / phản hồi vị trí của van nước, EXV, flap, AGS. Chỉ có cờ `VCU Valve component error level`, `VCU Ags component error level` → chỉ đếm và thống kê cờ lỗi, không phát hiện sớm được.
- **Output:**
  ```json
  {"vin": "VF000123", "actuator_id": "valve", "error_level_events_30d": 3}
  ```
- **Baseline gốc (khi có tín hiệu vị trí):** |lệnh − phản hồi| > ngưỡng kéo dài > T giây, hoặc đổi chế độ mà nhiệt không phản ứng.

#### B13. Lọc gió cabin tắc / blower yếu
- **Loại:** Luật + xu hướng
- **Khả thi:** 🔴 Thiếu tín hiệu. Không có công suất / tốc độ / điện áp blower nên baseline gốc không làm được. Có thể **tạm hoãn**, hoặc chỉ nhắc thay lọc theo thời gian / km.
- **Baseline gốc (khi có tín hiệu):** công suất blower ở mỗi mức gió so với baseline sau lần thay lọc gần nhất.

### 🟢 Ưu tiên 3: tầng toàn đội xe / tổng hợp

#### B14. Độ tin cậy linh kiện nhiệt (fleet / bảo hành)
- **Loại:** Thống kê (Weibull, Kaplan–Meier)
- **Khả thi:** ⚪ Cần dữ liệu ngoài telemetry (claim bảo hành, lô sản xuất, nhà cung cấp). Từ điển có part number / phiên bản phần mềm của ECU (nhóm `ECUs information`, `Climate Information → AC Part number`) giúp gom theo linh kiện.
- **Input:** claim bảo hành, DTC, lô sản xuất, nhà cung cấp, `odometer`, tuổi xe, vùng địa lý
- **Output:**
  ```json
  {"component": "ac_compressor", "supplier": "NCC_A", "weibull_beta": 1.8,
   "weibull_eta_km": 210000, "b10_km": 60000, "forecast_claims_next_q": 42}
  ```
- **Trùng:** bài 2 phát hiện sớm từ tín hiệu; B14 thuộc phía chất lượng / bảo hành.

#### B15. Điểm sức khỏe nhiệt tổng hợp + gợi ý bảo dưỡng
- **Loại:** Bộ luật (rule engine), gom output của bài 1–4 và B5–B13, cộng thêm các telltale có sẵn (`Cooling system malfunction`, `Climate control malfunction`)
- **Output:**
  ```json
  {"vin": "VF000123", "thermal_health_score": 68,
   "actions": ["Kiểm tra hệ điều hòa", "Kiểm tra nước làm mát"], "priority": "medium"}
  ```

> **Ngoài phạm vi:** cảnh báo cháy nổ pin (thermal runaway) thuộc nhóm Pin; chỉ ghi chú là có liên quan.

---

## 5. Kế hoạch dữ liệu giả (fake data)

- **Quy mô:** ~200 xe × 180 ngày, mẫu gộp về mỗi 10 giây; nhiều dòng xe (1 motor / 2 motor; có / không có heat pump nếu xác nhận được).
- **Chỉ sinh các tín hiệu có trong từ điển** (mục 6), đúng dạng của chúng: giá trị đo, cờ / trạng thái, hoặc số cộng dồn. Các đại lượng không có (áp suất gas, tốc độ máy nén…) vẫn có thể mô phỏng **bên trong** để sinh ra các tín hiệu nhìn thấy được, nhưng không xuất ra như một cột.
- **Thời tiết:** theo mùa của Hà Nội (có mùa đông) và TP.HCM (nóng quanh năm).
- **Mô hình vật lý đơn giản:**
  - Nhiệt cabin và nhiệt pin: mô hình bậc 1 (gia nhiệt từ môi trường/nắng/tải − công suất làm mát).
  - Áp suất gas (ẩn): bảng bão hòa R1234yf × hệ số lượng gas → ảnh hưởng tới nhiệt dàn lạnh.
  - Mức nước làm mát (ẩn) giảm tuyến tính khi có rò → bật cảnh báo thiếu nước khi dưới ngưỡng.
- **Lỗi được bơm vào, có nhãn:**

| Lỗi | Cách mô phỏng | Thấy được qua tín hiệu nào | Phục vụ bài |
|---|---|---|---|
| Rò gas chậm | Lượng gas giảm 1–5%/tháng | Nhiệt dàn lạnh cao dần, pull-down chậm dần | 3, 4, B7 |
| Bơm suy giảm | Lưu lượng hiệu dụng giảm dần | Chênh nhiệt nước vào/ra pin tăng, cell nóng hơn | 1, B6, B8 |
| Quạt két chết | Lưu lượng gió qua két = 0 khi xe đứng | Cờ lỗi quạt, nhiệt motor/EDS cao lúc đứng yên | 4, B8 |
| Chiller kém | Hiệu suất trao đổi nhiệt giảm | BMS yêu cầu làm mát mà nước pin không lạnh xuống | 4, B6, B9 |
| Rò nước làm mát | Mức nước giảm, nhiệt tăng | Cảnh báo thiếu nước / rò, nhiệt tăng | 1, B6 |
| Cảm biến lỗi | offset / drift / stuck | Chính giá trị cảm biến | B5 |
| Van / cửa gió kẹt | Vị trí cố định (ẩn) | Cờ lỗi van / AGS, nhiệt không theo chế độ | B12 |
| Lọc tắc | Lưu lượng gió giảm (ẩn) | Pull-down chậm ở cùng mức gió (tín hiệu yếu) | B13 |
| PTC hỏng | Công suất PTC = 0 (ẩn) | Cờ lỗi PTC, cabin không ấm lên | B10 |

- Mỗi lỗi có `fault_type`, `onset_time`, `severity` để chấm điểm (precision/recall, thời gian phát hiện sớm được bao lâu).

---

## 6. Từ điển trường telemetry (đối chiếu với `resource_dictionary_full.csv`)

Mã viết tắt, bỏ tiền tố `content.` (ví dụ `34183.1.7` = `content.34183.1.7`).
Trạng thái: ✅ có giá trị đo · 🟡 chỉ có cờ / trạng thái / số cộng dồn · ❌ không có trong từ điển.

> Danh sách đầy đủ **299 tín hiệu** (279 ban đầu + 20 bổ sung 10/2026: điện trở / cảnh báo cách điện pin, cờ lỗi IGBT, cửa sổ trời / rèm che, người ngồi, lịch & phiên điều hòa từ xa, SOC 12 V) liên quan nhóm Nhiệt & Điều hòa (kèm nhóm, loại, mức ưu tiên, bài toán dùng tới) nằm ở [`thermal_hvac_signals.csv`](thermal_hvac_signals.csv). Các bảng dưới đây chỉ là phần chính.

### Chung
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `vin` | VIN Number | 34180.1.1 | ✅ |
| `timestamp` | Timestamp | 34183.1.6 | ✅ |
| `vehicle_state` | Ignition Status; Vehicle High voltage Ready State; Gear Position | 34183.1.10; 34193.1.35; 34183.1.1 | ✅ |
| `speed` | Vehicle speed | 34183.1.2 | ✅ |
| `odometer` | Odometer | 34183.1.3 | ✅ |
| `soc` | HV Battery SOC (hoặc BMS Actual SOC) | 34183.1.9 (34220.1.2) | ✅ |
| `ambient_temp` | Ambient Temperature (+ External Temperature Fail Sts) | 34183.1.7 (34233.4.21) | ✅ |
| `parked_duration` | Parking duration | 34183.1.30 | ✅ |
| `accel_pedal` | Accelerator pedal position | 34183.1.26 | ✅ |
| `solar_load` | — | — | ❌ |

### Vòng gas lạnh
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `evap_temp` | Actual evaporator temperature of the HVAC unit | 34233.9.39 | ✅ |
| `ac_comp_fault` | EAC Compressor Fault Status failure | 34233.2.184 | 🟡 |
| `hvac_error_level` | VCU Hvac component error level | 34233.2.13 | 🟡 |
| `ac_comp_speed`, `ac_comp_speed_cmd`, `ac_comp_power` | — | — | ❌ |
| `ac_pressure_high`, `ac_pressure_low` | — (chỉ có High pressure interlock failure, đang Reserved) | (34233.2.199) | ❌ |
| `exv_cmd`, `exv_pos` | — | — | ❌ |
| `chiller_status` | — ; thay bằng `batt_cooling_request` | — | ❌ |

### Vòng nước pin
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `coolant_temp_batt_in` | Temperature of Battery Coolant Inlet | 34220.1.104 | ✅ |
| `coolant_temp_batt_out` | Temperature of Battery Coolant Outlet | 34220.1.105 | ✅ |
| `batt_cooling_request` | requesting the cooling power required for the battery pack | 34220.1.109 | ✅ |
| `batt_pump_state` | Battery electronic pump state (suy từ tên: trạng thái, không phải tốc độ — cần kiểm) | 34233.8.12 (34233.9.22) | 🟡 |
| `water_pump_fault` | Water pump failure; VCU Water pump component error level | 34233.2.192; 34233.2.16 | 🟡 |
| `preconditioning_status` | Battery pack precondition information (chưa rõ là cờ hay giá trị — cần kiểm) | 34233.4.4 | 🟡 |
| `ptc_error_flags` | PTC module failure; VCU Ptc component error level | 34233.2.198; 34233.2.10 | 🟡 |
| `warning_low_coolant` | Low level coolant water | 34200.7.1 | 🟡 |
| `coolant_leak_warning` | Coolant Leakage warning; Battery Coolant Leakage detected | 34220.1.97; 34200.6.14 | 🟡 |
| `batt_pump_speed`, `batt_pump_speed_cmd`, `batt_heater_status`, `coolant_level` | — | — | ❌ |

### Vòng nước motor
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `motor_pump_state` | Motor electronic pump state | 34233.8.11 (34233.9.17) | 🟡 |
| `motor_coolant_hot_flag` | EDS FR / RR Alarm when Cooling water temperature is too high | 34233.3.10 / 34233.3.34 | 🟡 |
| `fan_error_level` | VCU Fan component error level | 34233.2.9 | 🟡 |
| `valve_error_level` | VCU Valve component error level | 34233.2.11 | 🟡 |
| `ags_error_level` | VCU Ags component error level | 34233.2.6 | 🟡 |
| `coolant_temp_motor_in/out`, `motor_pump_speed`, `radiator_fan_duty/speed`, `coolant_valve_cmd/pos` | — | — | ❌ |

### Pin / motor / điện tử công suất
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `bms_max_cell_temp` / `bms_min_cell_temp` | Max / Min Cell Temperature (+ số hiệu đầu dò .77 / .79) | 34220.1.80 / 34220.1.78 | ✅ |
| `cell_temp_delta` | max and min cell temperature differences | 34220.1.81 | ✅ |
| `pack_temp` | Pack temperature | 34220.1.3 | ✅ |
| `motor_temp` | Motor Temperature (chưa rõ motor trước hay sau) | 34233.3.231 | ✅ |
| `eds_temp` (≈ `inverter_temp`) | EDS current temperature (cần xác nhận ý nghĩa) | 34233.3.232 | ✅ |
| `dcdc_current` | DCDC Output Current | 34233.9.35 | ✅ |
| `power_limit_flag` | Power limitation warning; VCU Electric Motor power reduced; BMS LOS request | 34200.1.68; 34200.9.6; 34220.1.70 | 🟡 |
| cờ quá nhiệt (thay `derate_reason`) | EDS FR/RR Motor over temperature alarm/fault; EDS over temperature alarm; IGBT junction over temperature; Battery high temperature warning; Delta temperature warning; Charger Over Temperature Fault; DCDC Over Temperature Fault | 34233.3.3/.4/.27/.28; 34233.3.9/.33; 34233.3.57/.58/.88/.89; 34200.1.31; 34220.1.99; 34233.2.213; 34233.9.25 | 🟡 |
| cờ drive plate quá nóng | EDS FR / RR Alarm when drive plate temperature is too high | 34233.3.56 / 34233.3.87 | 🟡 |
| `cell_temp_fault_flags` | cell overtemperature / undertemperature fault; Over / Under Temperature of the cell is detected | 34220.1.16 / 34220.1.17; 34233.2.242 / 34233.2.245 | 🟡 |
| `eds_temp_offset_alarm` | EDS FR / RR temp offset checkout alarm | 34233.3.11 / 34233.3.35 | 🟡 |
| `bms_temp_sensor_fault` | temperature sensor configuration fault; more than one / single temperature sensor electrical fault in a module | 34220.1.42; 34220.1.44 / 34220.1.45 | 🟡 |
| `torque` | EDS FR / RR actual output torque of current (+ cờ hợp lệ .147 / .152) | 34233.3.148 / 34233.3.153 | ✅ |
| cờ AGS kẹt | Active Grille Shutters stuck | 34200.2.32 | 🟡 |
| `eac_module_fault` | EAC Module failure | 34233.2.183 | 🟡 |
| `bdu_temp` | BDU Temperature | 34233.4.2 | ✅ |
| cờ pin đóng băng | EV Battery frozen | 34200.2.27 | 🟡 |
| giao tiếp CCU | CCU lost communication (telltale); NM CCUF / CCUR Body | 34200.1.24; 34233.2.156 / 34233.2.176 | 🟡 |
| `derate_reason` | — | — | ❌ |

### Sạc
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `charge_power` | Charging Power | 34220.1.118 | ✅ |
| `c_rate` | C Rate | 34220.1.117 | ✅ |
| `charge_current_allowed` (thay `charge_power_limit`) | Continuous maximum allowable charge current of battery | 34220.1.106 | ✅ |
| `charging_type` | Charging type; DC charging gun status | 34193.1.32; 34193.1.17 | ✅ |
| `fast_charge_longer_flag` | Super Fast Charge Longer | 34193.1.30 | 🟡 |
| `pack_cold_degrade_flag` | Pack Power Degrade: Battery is cold and limited capacity | 34220.1.93 | 🟡 |
| `battery_cold_flags` | EV Battery very cold condition; Battery low temperature warning | 34200.6.5; 34200.1.71 | 🟡 |

### HVAC cabin
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `cabin_temp` | Interior temperature | 34183.1.15 | ✅ |
| `cabin_setpoint` | Driver Temperature / Passenger Temperature | 34184.1.6 / 34184.1.7 | ✅ |
| `hvac_mode` | Driver AC Mode; Air Condition; Max AC | 34184.1.5; 34184.1.42; 34184.1.10 | ✅ |
| `blower_level` | Driver / Passenger Air Blow Level | 34184.1.25 / 34184.1.24 | ✅ |
| `recirc_mode` | Re-circulation | 34184.1.11 | ✅ |
| `air_flow` | Driver / Passenger Air Flow (hướng gió) | 34184.1.12 / 34184.1.26 | ✅ |
| `front_defrost` | Front Defrost | 34184.1.9 | ✅ |
| `climate_energy_acc` (thay `hvac_power`) | Accumulated Climate Energy Consumption | 34198.1.6 | 🟡 cộng dồn |
| `motor_energy_acc` | Accumulated Motor Energy Consumption | 34198.1.7 | 🟡 cộng dồn |
| `trip_avg_consumption` | Average Power Consumption (non-VFe34 / VFe34, theo chuyến) | 34187.1.5 / 34187.1.6 | ✅ |
| `flap_cmd` | Set Flap position (lệnh từ xa) | 34199.1.7 | 🟡 |
| `vent_outlet_temp`, `blower_power/speed/voltage`, `flap_pos`, `ptc_power`, `heat_pump_mode` | — | — | ❌ |

### Sự kiện / cảnh báo
| Tên nội bộ | Tín hiệu thật | Mã | |
|---|---|---|---|
| `dtc_code` | DTCs log (Target ECUs) | 34201.1.2 (34201.1.1) | ✅ |
| `cooling_system_malfunction` | Cooling system malfunction | 34200.11.1 | 🟡 |
| `climate_malfunction` | Climate control malfunction | 34200.11.2 | 🟡 |
| `tsen_error_level` | VCU Tsen component error level | 34233.2.12 | 🟡 |

> Một số telltale xuất hiện hai lần với mã khác nhau (ví dụ `34200.1.68` và `34200.25.28` đều là Power limitation warning) — có thể do khác dòng xe; cần hỏi lại team.

---

## 7. Các bước tiếp theo

1. ~~Đối chiếu mục 6 với danh sách trường telemetry thật của team.~~ Đã đối chiếu với `resource_dictionary_full.csv`.
2. Lấy **một mẫu dữ liệu thật** để kiểm tra: tín hiệu nào có dữ liệu, đơn vị, tần suất gửi, dòng xe nào gửi.
3. Xác nhận dòng xe nào có heat pump, dòng nào 2 motor (ảnh hưởng B8, B10).
4. ~~Chốt danh sách bài.~~ Đã chốt: **A. Sạc nhanh chậm vì nhiệt → B. Giảm công suất vì quá nhiệt → C. Sưởi kém** (xem đầu mục 4).
5. ~~Viết bộ sinh dữ liệu giả.~~ Đã có bản đầu trong `vinfast_thermal_3d.html` (Mô phỏng vận hành: đủ 279 tín hiệu + nhãn lỗi + cột kết quả phát hiện). Còn thiếu: chạy hàng loạt nhiều xe × nhiều ngày.
6. Làm baseline theo thứ tự A → B → C (kèm bước lọc cảm biến dùng chung), chỉnh ngưỡng trên mẫu dữ liệu thật.

## 8. Câu hỏi mở
- Tần suất gửi telemetry thực tế là bao nhiêu (1 giây, 10 giây, hay chỉ theo sự kiện)? Nhóm `Realtime Bus Monitoring` có gửi liên tục không?
- `EDS current temperature` (34233.3.232) là nhiệt inverter, nhiệt motor, hay nhiệt cả cụm? `Motor Temperature` (34233.3.231) là motor trước hay sau?
- Cờ `PTC module failure` / `VCU Ptc component error level` là PTC gió hay PTC nước (hay xe chỉ có một bộ)?
- Xe có cảm biến áp suất gas / tốc độ máy nén trên CAN không — nếu có, có thể xin bổ sung vào telemetry để làm B7?
- Giá trị của các trường "error level" và "pump state" mang ý nghĩa gì (bảng mã)?
- Có dữ liệu claim bảo hành / lịch sử xưởng dịch vụ để làm nhãn thật không?
- Đầu ra cuối cùng cần ở dạng nào: dashboard, cảnh báo cho xưởng, hay báo cáo định kỳ?
