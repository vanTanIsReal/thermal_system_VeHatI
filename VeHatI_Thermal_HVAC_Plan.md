# VeHatI – Nhóm Nhiệt & Điều hòa (Thermal & HVAC) · Kế hoạch v2

> Bản 2 (10/2026): viết lại theo hướng **VeHatI thông minh và thiết thực**. Bản cũ lưu ở [`VeHatI_Thermal_HVAC_Plan_v1.md`](VeHatI_Thermal_HVAC_Plan_v1.md).
> **Nguồn:** tên và mã tín hiệu lấy từ [`resource_dictionary_full.csv`](resource_dictionary_full.csv); danh sách 299 tín hiệu nhóm nhiệt ở [`thermal_hvac_signals.csv`](thermal_hvac_signals.csv). Cấu tạo hệ thống, lỗi hay gặp và cách làm là kiến thức kỹ thuật chung, **chưa đối chiếu với tài liệu sửa chữa VinFast**.
> **Chưa kiểm trên dữ liệu thật:** đơn vị, tần suất gửi, dòng xe nào gửi tín hiệu nào. Mọi ngưỡng trong tài liệu chọn trên dữ liệu mô phỏng, **phải chỉnh lại khi có mẫu thật**.

---

## 0. Tóm tắt một trang

**Mục tiêu.** Từ telemetry, phát hiện sớm và giải thích các vấn đề nhiệt mà **khách hàng thấy rõ**, rồi đưa ra việc cần làm cho đúng người (khách, xưởng, kỹ sư).

**Ba bài chốt** (bổ sung cho 4 bài đã có của team):

| | Bài | Khách hàng gặp | Vì sao chọn |
|---|---|---|---|
| A | **Sạc chậm vì nhiệt → bộ phận nào đang yếu → sức khỏe bộ phận trong tương lai** | Cắm sạc nhanh mà lâu hơn hẳn | Rất hay gặp (trưa nắng, sáng đông); đủ tín hiệu; đo được bằng **số phút mất**; từ đó soi được **hệ tản nhiệt của pin** và linh kiện đang yếu |
| B | **Xe bị giảm công suất vì quá nhiệt** | Xe đột nhiên yếu, đồng hồ báo giới hạn công suất | Ảnh hưởng an toàn và trải nghiệm; **dự báo trước được** nếu theo dõi hệ làm mát |
| C | **Sưởi kém / không sưởi** | Bật sưởi mà cabin vẫn lạnh, kính mờ lâu | Mùa đông miền Bắc; dễ giải thích, dễ kiểm chứng |

**"Thông minh" nghĩa là gì ở đây.** Không phải dùng mô hình phức tạp, mà làm được 3 việc mà luật đơn thuần không làm được:
1. **Báo trước** khi hỏng: "khoảng 3–4 tuần nữa xe này sẽ bắt đầu bị giới hạn công suất khi leo dốc".
2. **Nói được vì sao và ở đâu**: "70% do két nước bẩn, 20% do bơm motor yếu", kèm bằng chứng.
3. **Gợi ý việc cần làm** cho đúng người, và **học lại** từ kết quả sửa chữa thực tế.

**Lộ trình 3 giai đoạn:**

| Giai đoạn | Nội dung | Kết quả trình bày được |
|---|---|---|
| 1. Nền tảng | Lọc cảm biến sai, **baseline luật** cho A/B/C, sinh dữ liệu giả hàng loạt | Mỗi phiên sạc / sự kiện / chuyến đi có JSON kết luận; điểm số trên dữ liệu giả |
| 2. Dự báo | **Mô hình hành vi bình thường** (học từ xe khỏe): nhiệt motor, công suất sạc, hiệu quả làm mát pin, nhiệt dàn lạnh | **Báo sớm hơn luật bao nhiêu ngày**, tỉ lệ báo nhầm |
| 3. Chẩn đoán & hành động | Gộp bằng chứng ra nguyên nhân có xác suất, **điểm sức khỏe nhiệt**, gợi ý theo người nhận, học từ phiếu xưởng | Thẻ sức khỏe từng xe; phiếu chẩn đoán gửi xưởng |

**Cần từ team ngay:** một **mẫu dữ liệu thật** (vài xe × vài tuần), tần suất gửi telemetry, ý nghĩa cờ PTC (gió hay nước), dòng xe nào có heat pump / 2 motor, có lịch sử xưởng / bảo hành không (xem mục 9).

**Đã có sẵn** (giai đoạn 0):
- Danh sách 299 tín hiệu nhóm nhiệt, đã đối chiếu từ điển.
- Mô hình 3D + mô phỏng [`vinfast_thermal_3d.html`](vinfast_thermal_3d.html), gồm:
  - mô phỏng vận hành xuất CSV đủ cột tín hiệu, có nhãn lỗi;
  - chế độ "Hỏng hóc" theo A/B/C;
  - "Luồng hoạt động" từng bước.

  Giải thích chi tiết phần mô phỏng: [`giai_thich_mo_phong_3d.md`](giai_thich_mo_phong_3d.md).
- Hình 3D 26 bộ phận ở [`hinh_bo_phan/`](hinh_bo_phan/).

---

## 1. Nguyên tắc thiết kế

1. **Luật trước, ML sau.** Baseline luật chạy được ngay, dễ giải thích và là mốc so sánh. ML chỉ dùng khi hơn luật rõ ràng (báo sớm hơn, ít báo nhầm hơn).
2. **ML không cần nhãn lỗi.** Dùng **mô hình hành vi bình thường**: học trên xe khỏe để dự đoán giá trị *đáng lẽ phải có*, rồi theo dõi phần chênh. Không huấn luyện phân loại nguyên nhân trên dữ liệu giả, vì mô hình sẽ chỉ học lại cách mình bơm lỗi.
3. **Mọi kết luận kèm bằng chứng.** Ví dụ: "nước vào pin chỉ lạnh hơn cell 4°C trong khi BMS đang đòi làm mát".
4. **So với xe tương tự**, không dùng một ngưỡng chung: cùng dòng xe, cùng vùng, cùng tháng.
5. **Mỗi đầu ra có người nhận và chỉ số lợi ích**: phút sạc tiết kiệm, số lần xe bị giới hạn công suất, số lần thay nhầm linh kiện, chi phí bảo hành.
6. **Không làm phiền.** Chỉ gửi cho khách khi chắc chắn và có việc cụ thể để làm; còn lại gửi xưởng hoặc kỹ sư.

---

## 2. Bối cảnh: 4 bài đã có và vì sao chọn A/B/C

| # | Bài đã có | Khả thi với telemetry |
|---|---|---|
| 1 | Phát hiện rò / thiếu nước làm mát, bất thường vòng làm mát | ✅ (cảnh báo thiếu nước / rò, nhiệt nước vào/ra pin, cờ bơm) |
| 2 | Phát hiện sớm lỗi điều hòa theo dòng xe và mùa | 🟡 (cờ lỗi + nhiệt dàn lạnh / cabin) |
| 3 | Điều hòa kém lạnh nhận ra từ telemetry | 🟡 (không có áp suất gas, tốc độ máy nén) |
| 4 | Phân biệt kiểu hỏng: không đủ lạnh / không hoạt động / máy nén / quạt / chiller | 🟡 (chủ yếu qua cờ lỗi) |

**Tiêu chí chọn bài mới:** lỗi **khách dễ gặp và tự thấy rõ**, telemetry **đủ tín hiệu**, đầu ra **đo được**. A/B/C là ba bài thỏa cả ba. Các bài còn lại trong bản cũ (B5–B15) không bỏ mà được **gộp vào làm thành phần** của kiến trúc mới (xem Phụ lục C).

**Kiến trúc tổng thể:**

```
Telemetry (299 tín hiệu)
   │
   ▼
[Lọc cảm biến sai]  ← dùng chung (B5)
   │
   ├─► [Baseline luật A/B/C] ─────────────► sự kiện + kết luận (giai đoạn 1)
   │
   ├─► [Mô hình hành vi bình thường M1–M4] ► phần chênh + xu hướng + "còn bao lâu" (giai đoạn 2)
   │
   ▼
[Chẩn đoán gộp bằng chứng] ► nguyên nhân + xác suất + bằng chứng
   │
   ▼
[Điểm sức khỏe nhiệt + gợi ý hành động] ► khách (app) · xưởng (phiếu chẩn đoán) · kỹ sư (theo đội xe)
   ▲
   └── học lại từ phiếu xưởng / bảo hành (giai đoạn 3)
```

---

## 3. Ba bài chốt

Bước chung cho cả ba bài: **lọc cảm biến sai trước khi kết luận** (mục 4.1).

### A. Sạc chậm vì nhiệt → bộ phận nào đang yếu → sức khỏe bộ phận trong tương lai

**Phát biểu bài toán**

> Cách giải hiện tại, từng bước kèm ví dụ: [`bai_A_cach_giai.md`](bai_A_cach_giai.md). Công thức chi tiết và hướng ML: [`bai_A_cong_thuc_va_ML.md`](bai_A_cong_thuc_va_ML.md).

> Với mỗi phiên sạc nhanh DC, dùng telemetry để trả lời ba câu hỏi nối tiếp: **sạc chậm có phải do nhiệt không** (và mất bao nhiêu phút); **nếu do nhiệt thì bộ phận nào của hệ tản nhiệt đang yếu**; và **sức khỏe của bộ phận đó trong tương lai ra sao** (yếu dần nhanh cỡ nào, còn bao lâu thì gây sạc chậm rõ rệt).

- **Bối cảnh:**
  - Khi sạc nhanh, BMS tự giảm dòng sạc nếu pin quá nóng (trên khoảng 45°C) hoặc quá lạnh (dưới khoảng 15–20°C).
  - Pin quá nóng lúc sạc thường do **hệ tản nhiệt của pin làm việc kém** (chiller, gas, máy nén, quạt két, bơm pin, nước làm mát); pin quá lạnh do **không được làm ấm** (PTC nước, hoặc người dùng không bật làm ấm).
  - Khách chỉ thấy "sạc lâu". Các linh kiện này hỏng từ từ, **không có cờ lỗi** cho tới khi hỏng hẳn, nên hiện tại không ai biết xe nào đang xuống cấp.
- **Ba câu hỏi, trả lời theo thứ tự:**
  1. *(Tầng 1 – phát hiện)* Sạc chậm có phải **do nhiệt** không? Do pin nóng hay pin lạnh? Mất thêm bao nhiêu phút? (Do trạm sạc, SOC cao… thì dừng.)
  2. *(Tầng 2 – chẩn đoán, trọng tâm)* Nếu do nhiệt, **bộ phận nào đang yếu**? Hệ tản kém ở khâu nào (không phản ứng, nước không đủ lạnh, nước chảy kém, làm ấm kém) → ghép dấu vết ngoài phiên → bộ phận nghi ngờ kèm xác suất, xác nhận qua nhiều phiên. Bao nhiêu phút mất là do bộ phận đó, bao nhiêu do điều kiện? (Hệ tản ổn thì do điều kiện, dừng.)
  3. *(Tầng 3 – dự báo)* **Sức khỏe của bộ phận đó trong tương lai**: đang yếu đi nhanh cỡ nào, còn bao lâu thì gây sạc chậm rõ rệt, mùa tới mỗi lần sạc sẽ mất bao nhiêu phút?
- **Đơn vị phân tích:** mỗi phiên sạc nhanh DC (tầng 1; tầng 2 trong phiên, xác nhận bộ phận qua nhiều phiên); mỗi xe × tuần (tầng 3).
- **Đầu vào:**
  - Mỗi phiên: chuỗi thời gian (khoảng 10 giây / mẫu) gồm công suất, dòng, điện áp sạc; dòng cho phép và dòng BMS yêu cầu; SOC; loại sạc; nhiệt cell lớn nhất / nhỏ nhất; **nhiệt nước vào / ra tấm làm mát**; yêu cầu làm mát của BMS; trạng thái bơm pin; làm ấm pin; nhiệt ngoài trời.
  - Thêm cho tầng 2: nhiệt dàn lạnh điều hòa, cờ lỗi bộ phận (quạt, máy nén, bơm, van, PTC, thiếu nước). Thêm cho tầng 3: các phiên trước của chính xe đó, thời tiết điển hình các tháng tới.
- **Đầu ra:**
  - Tầng 1 (mỗi phiên): có chậm do nhiệt không, nóng hay lạnh, số phút mất.
  - Tầng 2 (mỗi phiên, xác nhận qua nhiều phiên): khâu kém, bộ phận nghi ngờ kèm xác suất, bằng chứng, phút mất do bộ phận / do điều kiện.
  - Tầng 3 (mỗi xe × tuần): sức khỏe của bộ phận nghi ngờ, xu hướng, "còn khoảng bao nhiêu tuần", phút mất dự kiến tháng tới.
- **Ngoài phạm vi:** sạc chậm do trạm sạc, do SOC cao, sạc AC; lỗi của bản thân cell pin (chuyển nhóm Pin; bài này chỉ nhận ra để loại trừ).
- **Ràng buộc:**
  - Không có lưu lượng nước, áp suất gas, trạng thái chiller → phải suy gián tiếp từ nhiệt độ.
  - Chưa có nhãn hỏng thật → đánh giá trên dữ liệu giả có cài lỗi, cờ có sẵn làm nhãn tham khảo, về sau là phiếu xưởng.
- **Thành công khi:**
  - Không báo nhầm ở xe khỏe.
  - Phát hiện đúng phiên chậm do nhiệt, loại được phiên chậm do trạm.
  - Chỉ ra được bộ phận đúng trong top-2.
  - Báo trước được nhiều tuần với lỗi phát triển dần.

```
TẦNG 1  PHÁT HIỆN   Sạc chậm có DO NHIỆT không? Nóng hay lạnh? Mất bao nhiêu phút?   (công suất, dòng cho phép / yêu cầu, nhiệt cell)
   │  không do nhiệt → dừng
   ▼
TẦNG 2  CHẨN ĐOÁN   Nếu do nhiệt, BỘ PHẬN NÀO đang yếu?                                (nước vào / ra, yêu cầu làm mát, bơm + dàn lạnh, cờ lỗi)
   │  hệ tản ổn (do điều kiện) → dừng
   ▼
TẦNG 3  DỰ BÁO      SỨC KHỎE bộ phận đó trong TƯƠNG LAI: yếu nhanh cỡ nào, còn bao lâu  (nhiều phiên theo tuần + thời tiết sắp tới)
```

**Tín hiệu.** Telemetry **không có lưu lượng nước**, chỉ có **nhiệt độ** nước vào / ra tấm làm mát; lưu lượng phải suy ra (mục A.2). **Không có công suất cho phép**, chỉ có **dòng cho phép**; công suất cho phép = dòng cho phép × điện áp pack.

| Vai trò | Tín hiệu | Mã |
|---|---|---|
| Tách phiên | Trạng thái sạc; loại sạc; súng sạc DC | `34193.1.5`; `34193.1.32`; `34193.1.17` |
| Kết quả sạc | Công suất sạc; dòng pack; điện áp pack; C-rate | `34220.1.118`; `34220.1.59`; `34220.1.60`; `34220.1.117` |
| **Ai hãm sạc** | Dòng sạc **cho phép** (BMS); dòng sạc **BMS yêu cầu** trạm cấp | `34220.1.106`; `34220.1.76` |
| Mốc so sánh | SOC | `34183.1.9` |
| Nhiệt pin | Cell lớn nhất / nhỏ nhất (+ số hiệu đầu đo); chênh nhiệt cell | `34220.1.80 / .78` (`.77 / .79`); `34220.1.81` |
| **Hệ tản** | Nhiệt nước vào / ra tấm làm mát | `34220.1.104 / .105` |
| **Lệnh cho hệ tản** | BMS yêu cầu công suất làm mát; trạng thái bơm pin; làm ấm pin | `34220.1.109`; `34233.8.12`; `34233.4.4` |
| Môi trường | Nhiệt ngoài trời | `34183.1.7` |
| Nhãn tham khảo | Sạc lâu hơn; pin lạnh bị hạn chế | `34193.1.30`; `34220.1.93` |
| Dấu vết phụ (tầng 3) | Nhiệt dàn lạnh; cờ quạt két, máy nén, thiếu nước, van, bơm, PTC | `34233.9.39`; `34233.2.9`, `34233.2.184`, `34200.7.1`, `34233.2.11`, `34233.2.192`, `34233.2.198` |

#### A.1 Tầng 1 – Phát hiện: sạc chậm có do nhiệt không

1. **Tách phiên:** từ lúc trạng thái sạc bật tới lúc tắt, chỉ lấy sạc DC. Bỏ phiên < 5 phút hoặc mất nhiều dữ liệu.
2. **Ai đang hãm sạc?** So ba dòng điện cùng lúc:
   ```
   I_thực      = dòng pack thực tế              (34220.1.59)
   I_yêu_cầu   = dòng BMS xin trạm cấp          (34220.1.76)
   I_cho_phép  = dòng BMS cho phép tối đa       (34220.1.106)

   I_thực ≪ I_yêu_cầu                        → TRẠM SẠC yếu / chia công suất  (không do nhiệt)
   I_thực ≈ I_yêu_cầu, I_cho_phép bị tụt      → PIN đang bị BMS hãm            (xét tiếp nhiệt)
   ```
3. **Hãm vì nóng hay lạnh:**
   - cell lớn nhất > ~45°C → `pin_nong`;
   - cell nhỏ nhất < ~15–20°C → `pin_lanh`;
   - nhiệt bình thường mà vẫn hãm → nguyên nhân khác (SOC cao, lệch cell…), không tính vào bài.
4. **Số phút mất:**
   ```
   P_chuẩn(SOC)      = công suất của xe khỏe khi pin 20–35°C, tại mức SOC đó (cùng dòng xe)
                       → từ spec, hoặc phân vị 90 các phiên có pin trong vùng tốt
   Thời gian đáng lẽ = Σ năng lượng nạp ở từng khoảng SOC / min(P_chuẩn(SOC), P_trạm)
   Phút mất do nhiệt = Thời gian thực − Thời gian đáng lẽ    (chỉ tính các đoạn pin bị hãm vì nóng / lạnh)
   ```
   Phiên **bị giới hạn do nhiệt** khi công suất thực / chuẩn < 0,85 kéo dài ≥ 2 phút trong lúc pin nóng / lạnh.

#### A.2 Tầng 2 – Chẩn đoán: bộ phận nào đang yếu (trọng tâm)

Làm theo 3 bước: **khâu nào của hệ tản kém** (trong phiên, năm chỉ số dưới đây) → **bộ phận nào** (ghép dấu vết ngoài phiên) → **xác nhận** (lặp lại qua nhiều phiên).

**Chuỗi hoạt động của một phiên khỏe:**
```
pin nóng lên → BMS xin làm mát (34220.1.109 > 0) → bơm pin chạy (34233.8.12)
→ máy nén + chiller làm lạnh nước → NƯỚC VÀO pin lạnh xuống (34220.1.104)
→ nước chạy dưới đáy pin, hút nhiệt → NƯỚC RA ấm hơn (34220.1.105)
→ cell ngừng tăng / giảm dần (34220.1.80)
```
Hệ tản bất thường là **một mắt xích không xảy ra, xảy ra chậm, hoặc xảy ra yếu**.

**Năm chỉ số**, tính trong các đoạn **BMS đang xin làm mát**, so với **xe khỏe ở cùng điều kiện** (cùng dòng sạc, cùng nhiệt ngoài trời):

| # | Chỉ số | Công thức | Khỏe | Bất thường nghĩa là |
|---|---|---|---|---|
| ① | **Độ trễ phản ứng** | Thời gian từ lúc BMS xin làm mát → nước vào giảm được ≥ 3°C | Vài phút | Rất chậm / không giảm → nguồn lạnh không chạy (máy nén, van chiller, gas). Bơm báo tắt khi BMS đang xin → lỗi điều khiển bơm |
| ② | **Độ lạnh của nước** | `T_cell_max − T_nước_vào` | ≥ 7–10°C khi làm mát mạnh | Nhỏ (< 80% mức xe khỏe; mô phỏng < 7,9°C) → **nước không được làm lạnh đủ**: chiller, gas, máy nén, quạt két / dàn nóng |
| ③ | **Độ nóng lên của nước** (thay cho lưu lượng) | `T_nước_ra − T_nước_vào`, so với xe khỏe **ở cùng dòng sạc** | Khoảng vài độ | Lớn hơn bình thường + **chênh nhiệt cell tăng** (`34220.1.81`) → **nước chảy chậm**: bơm yếu, thiếu nước, có khí, tắc |
| ④ | **Hệ số tản nhiệt `k`** và **hệ số sinh nhiệt `a`** | Hồi quy trên các mẫu của phiên: `dT_cell/dt = a·I² − k·(T_cell − T_nước_vào) − b·(T_cell − T_ngoài)` | `k` ≈ mức của chính xe lúc mới | `k` giảm → tấm làm mát / dòng nước lấy nhiệt kém. `a` tăng dần mà `k` bình thường → **pin lão hóa**, không phải lỗi hệ tản |
| ⑤ | **Nhiệt cân bằng dự kiến** | `T_cân_bằng ≈ T_nước_vào + a·I² / k` | < 45°C ở dòng sạc đang dùng | > 45°C → BMS **chắc chắn phải hãm**: giải thích *vì sao* phiên chậm |

**Tách phút mất theo nguyên nhân:** chạy lại công thức ⑤ với `k` và nhiệt nước vào **của xe khỏe**. Thời gian sạc chênh lệch = **phút mất do hệ tản kém**; phần còn lại = **phút mất do điều kiện** (trời nóng, vừa chạy xa, sạc công suất rất lớn).

**Kết luận cho mỗi phiên:**
- `binh_thuong`: phản ứng nhanh, nước đủ lạnh, nước chảy đủ, `k` bình thường. Nếu vẫn chậm là do **tải nhiệt cao**.
- `nuoc_khong_du_lanh`: ② xấu, ③ bình thường.
- `nuoc_chay_kem`: ③ xấu, `k` giảm, chênh cell tăng.
- `khong_phan_ung`: ① xấu (BMS xin mà nước vào không đổi, hoặc bơm không chạy).
- Pin lạnh: `lam_am_kem` (đã làm ấm mà nước vào không ấm lên) hoặc `khong_lam_am_truoc` (do cách dùng).

Ví dụ hai phiên cùng điều kiện (trời 34°C, trạm 150 kW, SOC 20 → 80%; số liệu minh họa):

| | Phiên xe khỏe | Phiên xe có vấn đề |
|---|---|---|
| Cell lớn nhất cao nhất | 43°C | 49°C |
| Nước vào khi đang làm mát | 27°C | 40°C |
| ② Độ lạnh của nước | 16°C | 9°C → **xấu** |
| ③ Nước ra − vào | 3°C | 3°C → bình thường |
| Thời gian sạc | 28 phút | 37 phút → **mất 9 phút** |
| Kết luận | Bình thường | `nuoc_khong_du_lanh` |

**Từ khâu kém → bộ phận nghi ngờ** (ghép dấu vết ngoài phiên sạc):

| Khâu kém (trong phiên) | Dấu vết thêm để tách | Bộ phận nghi |
|---|---|---|
| Nước không đủ lạnh | Dàn lạnh cabin **cũng ấm** khi bật điều hòa (`34233.9.39`) | **Thiếu gas / máy nén** (có cờ `34233.2.184` → máy nén) |
| Nước không đủ lạnh | Dàn lạnh bình thường; có cờ quạt `34233.2.9` | **Quạt két** (sạc là lúc xe đứng yên, phụ thuộc quạt) |
| Nước không đủ lạnh | Dàn lạnh bình thường, không cờ, kém dần theo tuần | **Chiller đóng cặn / van chiller** (không tách được hai cái này) |
| Nước chảy kém | Cờ thiếu nước `34200.7.1`; vòng motor cũng nóng hơn | **Thiếu nước / rò / có khí** |
| Nước chảy kém | Không cờ thiếu nước; cờ `34233.2.192` nếu hỏng hẳn | **Bơm pin yếu** |
| Nước vào **nóng bất thường từ đầu phiên** | Cờ van `34233.2.11` | **Van 4 ngả kẹt** (nước nóng của motor lọt sang pin) |
| Pin lạnh, đã làm ấm mà nước vào không ấm lên | Cờ PTC `34233.2.198` | **PTC nước** |
| Một cảm biến lệch hẳn khi xe đỗ nguội | So nước vào / ra / cell sau khi đỗ ≥ 6 giờ | **Cảm biến** (loại ra trước khi kết luận) |
| `a` tăng dần, `k` bình thường | — | Không phải hệ tản: **pin lão hóa** (chuyển nhóm Pin) |

**Xác nhận:** chỉ kết luận bộ phận khi cùng khâu kém **lặp lại ≥ 3 phiên**. Xác suất cho từng bộ phận lấy theo cách gộp bằng chứng ở mục 4.3; cập nhật khi có phiếu xưởng.

#### A.3 Tầng 3 – Dự báo: sức khỏe bộ phận đó trong tương lai

Theo dõi **chỉ số sức khỏe ứng với bộ phận nghi ngờ** qua các tuần: nguồn lạnh (chiller, gas, máy nén, quạt / dàn nóng), dòng nước (bơm, thiếu nước), hệ tản nói chung (`k`).

**Chỉ số sức khỏe theo tuần** (trung vị các phiên có làm mát, quy về điều kiện chuẩn):
```
Sức khỏe nguồn lạnh = Độ lạnh của nước (②) hiện tại / lúc xe mới
Sức khỏe dòng nước  = Độ nóng lên của nước (③) lúc xe mới / hiện tại
Sức khỏe tản nhiệt  = k hiện tại / k lúc xe mới
```

**Dự báo "còn bao lâu":**
```
k_nguy_hiểm     = mức k mà một phiên sạc trưa hè chuẩn (35°C, 150 kW) có T_cân_bằng > 45°C
Số tuần còn lại = (k_hiện_tại − k_nguy_hiểm) / tốc_độ_giảm_mỗi_tuần     (kèm khoảng tin cậy)
```
Ví dụ: *"Hệ tản pin còn 72%, giảm 3%/tuần; khoảng 4–6 tuần nữa sạc trưa hè sẽ mất trên 10 phút mỗi lần."*

**Phút mất dự kiến mùa tới:** lấy sức khỏe dự kiến của bộ phận ở tháng tới + thời tiết điển hình + thói quen sạc của xe, tính lại một phiên điển hình → *"nếu không sửa, tháng 5 mỗi lần sạc trưa mất khoảng 12 phút"*.

**Dự báo được hay không:** bộ phận **xuống cấp từ từ** (chiller đóng cặn, rò gas chậm, bơm mòn, dàn nóng bẩn, rò nước chậm) thì dự báo được. Bộ phận **hỏng đột ngột** (quạt chết, PTC cháy, van kẹt) thì chỉ phát hiện khi xảy ra; ở cấp đội xe ước rủi ro theo tuổi / lô linh kiện khi có dữ liệu bảo hành.

#### A.4 Đầu ra

```json
{"session_id": "S-88812", "vin": "VF000123", "start": "2026-04-15 13:05",
 "tang1_phat_hien": {"cham_do_nhiet": true, "ly_do": "pin_nong", "phut_mat": 9.0},
 "tang2_chan_doan": {"khau_kem": "nuoc_khong_du_lanh",
                     "bo_phan_nghi": [{"bo_phan": "chiller_hoac_van_chiller", "p": 0.55}, {"bo_phan": "quat_ket", "p": 0.25}, {"bo_phan": "thieu_gas", "p": 0.2}],
                     "bang_chung": {"phan_ung_sau_phut": 4, "do_lanh_nuoc_c": 9.0, "nuoc_ra_tru_vao_c": 3.1, "k": 0.62, "k_chuan": 0.85, "t_can_bang_du_kien_c": 49},
                     "so_phien_lap_lai": 4, "phut_mat_do_bo_phan": 6.5, "phut_mat_do_dieu_kien": 2.5},
 "tang3_du_bao": {"chi_so": "suc_khoe_nguon_lanh", "suc_khoe": 0.73, "xu_huong_moi_tuan": -0.03,
                  "con_khoang_tuan": [4, 6], "phut_mat_du_kien_thang_toi": 12}}
```
`ly_do ∈ {pin_nong, pin_lanh, tram_sac, khac}` · `khau_kem ∈ {khong_co (do điều kiện), khong_phan_ung, nuoc_khong_du_lanh, nuoc_chay_kem, lam_am_kem, khong_lam_am_truoc}`

#### A.5 Theo giai đoạn của kế hoạch

| Giai đoạn | Làm gì cho bài A |
|---|---|
| 1. Nền tảng | Tầng 1 đầy đủ; tầng 2 phần khâu kém bằng ngưỡng (①②③⑤ với `k` tính theo phiên) |
| 2. Dự báo | Tầng 3: chỉ số sức khỏe theo tuần + xu hướng → "còn bao lâu", phút mất mùa tới (mô hình M3); đường sạc chuẩn bằng mô hình (M2) thay bảng tra |
| 3. Chẩn đoán & hành động | Tầng 2 đầy đủ: gộp dấu vết → bộ phận kèm xác suất, học từ phiếu xưởng; gợi ý hành động |

**Hành động:**
- **Khách:** giải thích vì sao sạc chậm. Mùa đông nhắc bật làm ấm pin, kèm ước tính "tiết kiệm khoảng N phút".
- **Xưởng:** hệ tản `bat_thuong` lặp lại ≥ 3 phiên, hoặc "còn ≤ 4 tuần" → phiếu kiểm tra theo linh kiện nghi ngờ (chiller / van chiller, gas, quạt két, bơm pin, mức nước, van 4 ngả, PTC nước).
- **Kỹ sư:** phân bố phút mất và sức khỏe hệ tản theo dòng xe, khí hậu, lô linh kiện; chỉnh ngưỡng bật làm mát / làm ấm.

#### A.6 Đánh giá

- **Tầng 1:** phát hiện phiên bị hãm vì nhiệt (precision / recall); sai số số phút mất. Nhãn tham khảo: `Super Fast Charge Longer`.
- **Tầng 2:** với lỗi cài vào dữ liệu giả (chiller, gas, quạt, bơm, thiếu nước, van, PTC nước): đúng khâu kém, đúng bộ phận top-1 / top-2; xe khỏe có bị báo nhầm không.
- **Tầng 3:** báo trước được bao nhiêu tuần, sai số "còn X tuần", độ phủ khoảng tin cậy (đánh giá bằng cách tua lại thời gian). Về sau đối chiếu phiếu xưởng.

#### A.7 Giới hạn

1. Không có lưu lượng, áp suất gas, trạng thái chiller → một số cặp **không tách được** (chiller với van chiller). Đầu ra ghi rõ "chưa phân biệt được".
2. Nhiệt cell thường làm tròn **1°C**, mẫu khoảng 10 giây → `k` phải tính trên đoạn đủ dài (≥ 10 phút).
3. Ngưỡng (45°C, 7°C, 3°C…) là ước lượng, **phải chỉnh trên dữ liệu thật**; nên so với xe cùng dòng thay vì ngưỡng cứng.
4. Cần biết **cách mã hóa** của "yêu cầu làm mát", "trạng thái bơm", "dòng BMS yêu cầu".

**Linh kiện liên quan:**
- **Chính:** pin, BMS, cảm biến nhiệt cell / nước vào–ra.
- **Hệ tản pin:** chiller, van chiller, máy nén, gas, dàn nóng, quạt két, bơm pin, van 4 ngả, bình nước phụ, ống & kẹp.
- **Làm ấm:** PTC nước.
- **Cần loại trừ:** trạm sạc, cổng sạc, contactor, BDU.

### B. Xe bị giảm công suất vì quá nhiệt

- **Câu hỏi:** xe nào hay bị giới hạn công suất vì nóng, ở motor/EDS hay pin, do điều kiện chạy hay do hệ làm mát kém, và **xe nào sắp bị**?
- **Đơn vị phân tích:** mỗi sự kiện giới hạn công suất; xu hướng hệ làm mát theo xe × tuần.
- **Tín hiệu:**
  - **Sự kiện:** đèn báo giới hạn công suất `34200.1.68 / 34200.25.28`, `34200.9.5`; giảm công suất motor `34200.9.6`; BMS yêu cầu chế độ giới hạn `34220.1.70`.
  - **Nhiệt:** nhiệt motor / EDS `34233.3.231 / .232`; cờ quá nhiệt IGBT, drive plate, nước làm mát EDS `34233.3.57 / .58 / .88 / .89 / .56 / .87 / .10 / .34`.
  - **Tải và chạy:** mô-men thực `34233.3.148 / .153`, tốc độ `34183.1.2`, bàn đạp ga `34183.1.26`, nhiệt ngoài trời `34183.1.7`.
  - **Hệ làm mát:** trạng thái bơm motor `34233.8.11`, cờ quạt két `34233.2.9`, cờ thiếu nước `34200.7.1`.
  - **Pin:** cell lớn nhất `34220.1.80`, dòng xả cho phép `34220.1.107`.
  - **Chuẩn hóa:** odometer `34183.1.3`.

**Giai đoạn 1 – baseline luật**
1. Sự kiện = đèn báo giới hạn công suất bật; các lần bật cách nhau < 2 phút gộp làm một.
2. Nguồn:
   - cờ quá nhiệt EDS / IGBT / nước làm mát EDS → `motor_eds`;
   - cell lớn nhất > 50°C, hoặc BMS yêu cầu giới hạn, hoặc dòng xả cho phép giảm → `pin`.
3. Nguyên nhân:
   - nhiệt ngoài trời > 38°C → `moi_truong_nong`;
   - mô-men hoặc ga > phân vị 90 trong 5 phút trước sự kiện → `tai_nang`;
   - còn lại → `he_lam_mat_kem`, kèm gợi ý nếu có cờ quạt / thiếu nước.
4. Xếp hạng xe theo số sự kiện / 1000 km so với xe cùng dòng.

**Giai đoạn 2 – dự báo** (mô hình M1, **bài ML chính**)
- **M1 dự đoán nhiệt motor / EDS** từ tải, tốc độ, nhiệt ngoài trời, trạng thái bơm; học trên xe khỏe.
- Mỗi ngày lấy **phần chênh** (nhiệt thực − dự đoán) ở các đoạn tải tương đương. Chênh tăng dần qua các tuần nghĩa là két bẩn, bơm yếu hoặc thiếu nước.
- **"Còn bao lâu":** dùng M1 với phần chênh hiện tại để mô phỏng một **kịch bản chuẩn nặng** (leo dốc 15 phút, 38°C). Kéo dài xu hướng phần chênh để ước lượng ngày mà nhiệt trong kịch bản đó chạm ngưỡng giới hạn → `eta_days`.
- Luật giai đoạn 1 chỉ phản ứng khi đèn đã bật. M1 cảnh báo **trước khi** khách bị.

**Giai đoạn 3 – chẩn đoán & hành động**
- Phân biệt bằng hình mẫu:
  - **quạt két / két bẩn:** kém rõ khi xe chạy chậm / đứng, đỡ hơn khi chạy nhanh (gió tự nhiên qua két);
  - **bơm yếu / thiếu nước:** kém ở mọi tốc độ.
- **Khách:** giải thích "xe giới hạn công suất để bảo vệ motor"; gợi ý đặt lịch vệ sinh két trước mùa hè.
- **Xưởng:** phiếu chẩn đoán khi `eta_days` ≤ 30 hoặc xe ở phân vị > 95: kiểm tra két, quạt, bơm motor, mức nước, van chia nước, AGS.
- **Kỹ sư / chất lượng:** tỉ lệ theo lô motor / inverter / két; ngưỡng giới hạn theo tuyến đường (đèo, cao tốc).

**Đầu ra**
```json
{"vin": "VF000123", "month": "2026-10", "derate_events_per_1000km": 4.2, "derate_minutes_total": 37,
 "source": "motor_eds", "main_cause": "he_lam_mat_kem", "fleet_percentile": 97,
 "cooling_residual_c": 6.5, "residual_trend_c_per_week": 0.8, "eta_days": 25,
 "suspects": [{"part": "ket_nuoc_ban", "p": 0.7}, {"part": "bom_motor", "p": 0.2}]}
```
`source ∈ {motor_eds, pin}` · `main_cause ∈ {moi_truong_nong, tai_nang, he_lam_mat_kem}`

**Đánh giá**
- **Thời gian báo sớm** (bao nhiêu ngày trước sự kiện đầu tiên), so với luật.
- **Báo nhầm** trên 1000 xe-tháng.
- Sai số M1 trên xe khỏe.
- Lỗi bơm vào dữ liệu giả **phát triển dần**: két bẩn, bơm mòn, rò nước, quạt chết.

**Lưu ý:** sự kiện hiếm trên từng xe. Phần dự báo (M1) không cần chờ sự kiện, nên vẫn chạy được trên mọi xe.

**Linh kiện liên quan**
- **Chính:** motor trước / sau, inverter / EDS.
- **Làm mát:** bơm nước motor, két nước, quạt két, AGS, van chia nước, bình nước phụ, ống & kẹp.
- **Cùng vòng nước:** OBC, DC-DC.
- **Khi nguồn là pin:** toàn bộ hệ làm mát pin (như bài A).

### C. Sưởi kém / không sưởi

- **Câu hỏi:** xe nào bật sưởi mà cabin không ấm lên được, và nghi bộ phận nào?
- **Đơn vị phân tích:** mỗi chuyến có bật sưởi ≥ 10 phút; tổng hợp theo xe × mùa.
- **Tín hiệu:** chế độ điều hòa `34184.1.5` · nhiệt cabin `34183.1.15` · nhiệt cài đặt `34184.1.6` · nhiệt ngoài trời `34183.1.7` · mức gió `34184.1.25` · hướng gió `34184.1.12` · sấy kính trước `34184.1.9` · cờ lỗi PTC `34233.2.198 / 34233.2.10` · lỗi điều hòa `34200.11.2`.

**Giai đoạn 1 – baseline luật**
1. `time_to_setpoint`: thời gian cabin tới gần nhiệt cài đặt, chuẩn hóa theo nhiệt ngoài trời và mức gió, so với xe cùng dòng / cùng ngày / cùng vùng.
2. Sau 10 phút sưởi mà cabin vẫn thấp hơn cài đặt > 5°C → `kem_nong`.
3. Nguyên nhân: có cờ PTC → `ptc`; không có cờ → nghi cửa gió trộn / blower / PTC yếu.

**Giai đoạn 2 – (tùy chọn)** mô hình M5 dự đoán `time_to_setpoint`. Dữ liệu ít (chỉ mùa đông miền Bắc) nên **luật là đủ**; chỉ làm khi có dữ liệu nhiều mùa.

**Giai đoạn 3 – chẩn đoán & hành động**
- PTC hỏng thường kéo theo **bài A mùa đông** (nếu PTC gió và nước dùng chung mạch, hoặc cả hai cùng hỏng): pin lạnh → sạc chậm. Gộp hai bằng chứng này để tăng độ chắc.
- **Khách:** gợi ý bật sưởi trước qua app; báo khi PTC có lỗi.
- **Xưởng:** có cờ PTC → kiểm tra / thay PTC; không có cờ → kiểm tra cửa gió trộn, blower, lọc gió, cảm biến nhiệt cabin.

**Đầu ra**
```json
{"vin": "VF000123", "date": "2026-01-10", "heating_status": "kem_nong", "time_to_setpoint_min": null,
 "cabin_gap_after_10min_c": 11.8, "suspected_cause": "ptc",
 "evidence": ["cờ PTC module failure", "cabin thấp hơn cài đặt 11,8°C sau 10 phút"]}
```
`heating_status ∈ {binh_thuong, cham, kem_nong, khong_suoi}` · `suspected_cause ∈ {ptc, cua_gio_tron, blower, chua_ro}`

**Đánh giá:**
- Phát hiện chuyến sưởi kém (precision / recall) trên lỗi bơm vào (PTC hỏng, cửa gió kẹt).
- Đối chiếu cờ PTC.
- Phiếu xưởng mùa đông.

**Lưu ý:** xe có heat pump sưởi khác PTC; cần biết dòng nào có heat pump.

### Ma trận linh kiện × bài chốt

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

---

## 4. Lớp "thông minh" dùng chung

### 4.1 Lọc cảm biến sai (làm đầu tiên)

Mọi kết luận đều dựa vào cảm biến, nên lọc trước.

- **Kiểm tra khi xe nguội** (đỗ ≥ 6 giờ): mọi cảm biến nhiệt phải xấp xỉ nhau. Cảm biến lệch > 3°C so với trung vị → `offset`, loại số đo đó khỏi các bài.
- **Đứng giá trị:** phương sai ≈ 0 trong nhiều giờ khi xe đang chạy → `stuck`.
- **Trôi dần:** độ lệch tăng theo thời gian → `drift`.
- **Nhãn đối chiếu** (cờ có sẵn): `VCU Tsen component error level`, `External Temperature Fail Sts`, `EDS FR/RR temp offset checkout alarm`, cờ cảm biến nhiệt của BMS.

```json
{"vin": "VF000123", "sensor": "34220.1.104", "fault_type": "offset", "offset_c": 6.2, "first_seen": "2026-09-14"}
```

### 4.2 Mô hình hành vi bình thường (ML giai đoạn 2)

**Cách chung:**
1. Huấn luyện **chỉ trên dữ liệu xe khỏe**: không có cờ lỗi, 30–60 ngày đầu sau giao xe hoặc sau bảo dưỡng.
2. Dự đoán giá trị *đáng lẽ phải có* từ điều kiện vận hành.
3. Theo dõi **phần chênh** (thực − dự đoán) theo ngày / tuần.
4. Dùng độ dốc xu hướng để ước lượng "còn bao lâu".
5. Mô hình đơn giản: hồi quy tuyến tính hoặc gradient boosting (LightGBM). **Không cần deep learning.**

| Mô hình | Dự đoán gì | Từ những gì | Phục vụ | Phần chênh tăng dần nghĩa là |
|---|---|---|---|---|
| **M1** | Nhiệt motor / EDS (hoặc tốc độ tăng nhiệt) | Mô-men, tốc độ, ga, nhiệt ngoài trời, nhiệt 5 phút trước, trạng thái bơm | **B** (chính) | Két bẩn, quạt yếu, bơm motor yếu, thiếu nước |
| **M2** | Công suất sạc kỳ vọng | SOC, cell max/min, nhiệt ngoài trời, loại trạm / công suất tối đa của phiên | **A** | (Không phải xu hướng) tính phút mất chính xác, tách phần do trạm |
| **M3** | Hệ số tản nhiệt `k` của pin (và hệ số sinh nhiệt `a`) từ cân bằng nhiệt trong phiên sạc | Dòng pack, nhiệt cell, nhiệt nước vào, nhiệt ngoài trời, trạng thái bơm | **A** (tầng 2–3), B6 | `k` giảm: chiller, gas, quạt, bơm pin, thiếu nước đang kém dần; `a` tăng: pin lão hóa |
| **M4** | Nhiệt dàn lạnh khi điều hòa chạy ổn định | Nhiệt ngoài trời, nhiệt cabin, nhiệt cài đặt, mức gió, gió hồi, tốc độ xe | B7 rò gas chậm, bài 3 | Thiếu gas / máy nén (mọi tốc độ) hoặc dàn nóng / quạt (chủ yếu khi chạy chậm) |
| M5 (tùy chọn) | Thời gian cabin đạt nhiệt cài đặt khi sưởi | Nhiệt ngoài trời, mức gió, nhiệt cài đặt | **C** | PTC yếu, cửa gió, blower |

**Vì sao chọn cách này:**
- Không cần nhãn lỗi.
- Có rất nhiều dữ liệu (mỗi phút chạy là một mẫu).
- Mang từ dữ liệu giả sang dữ liệu thật được ngay, vì mô hình không học cách mình bơm lỗi.
- Dễ giải thích: "nhiệt motor cao hơn mức bình thường của chính xe này 6,5°C ở cùng tải".

### 4.3 Chẩn đoán nguyên nhân bằng cách gộp bằng chứng

Mỗi bài cho ra các **bằng chứng**. Gộp chúng lại để xếp hạng nguyên nhân kèm xác suất, theo cách Bayes đơn giản:
- **Xác suất ban đầu** lấy từ kiến thức kỹ thuật (bảng dưới).
- **Cập nhật** khi có phiếu xưởng xác nhận, tức là đếm lại tần suất thực tế. Đây là chỗ **hệ thống tự học**.

| Bằng chứng ↓ / Nguyên nhân → | Thiếu gas | Máy nén | Quạt / dàn nóng bẩn | Chiller | Bơm pin | Thiếu nước / rò | Két nước bẩn | Bơm motor | Van chia nước kẹt | PTC nước | PTC gió | Cửa gió trộn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Làm mát pin kém (A, M3) | ●● | ●● | ● | ●● | ● | ● | | | ● | | | |
| Dàn lạnh ấm hơn kỳ vọng (M4) | ●● | ●● | ● | | | | | | | | | |
| Kém rõ khi xe đứng / chạy chậm | | | ●● | | | | ●● | | | | | |
| Nước ra – vào pin chênh lớn | | | | | ●● | ●● | | | | | | |
| Motor / EDS nóng hơn kỳ vọng (M1) | | | ●● | | | ●● | ●● | ●● | ● | | | |
| Pin lạnh dù đã làm ấm | | | | | | | | | ● | ●● | | |
| Cabin không ấm khi sưởi | | | | | | | | | | ● | ●● | ●● |
| Cờ lỗi riêng của bộ phận | | EAC `34233.2.184` | Quạt `34233.2.9` | | Bơm `34233.2.192` | Thiếu nước `34200.7.1` | | Bơm `34233.2.192` | Van `34233.2.11` | PTC `34233.2.198` | PTC `34233.2.198` | |

●● thường đi kèm · ● đôi khi

**Ví dụ:**
- Làm mát pin kém **và** dàn lạnh ấm, ở mọi tốc độ → thiếu gas / máy nén. Có cờ EAC thì là máy nén.
- Chỉ làm mát pin kém, dàn lạnh bình thường → chiller hoặc bơm pin. Nước ra–vào chênh lớn thì nghiêng về bơm / thiếu nước.
- Motor nóng hơn kỳ vọng, kém rõ khi chạy chậm → quạt két / két bẩn. Kém ở mọi tốc độ → bơm motor / thiếu nước.

**Giới hạn:** không có áp suất gas, tốc độ máy nén, vị trí van / cửa gió. Một số cặp nguyên nhân (ví dụ chiller với van chiller) chưa tách được; đầu ra phải ghi rõ "chưa phân biệt được".

### 4.4 Điểm sức khỏe nhiệt và gợi ý hành động

**Điểm sức khỏe** (0–100) cho từng xe, gồm các điểm thành phần, mỗi thành phần lấy từ phần chênh / xu hướng / sự kiện:
- làm mát pin (A, M3);
- làm mát motor (B, M1);
- điều hòa (M4, bài 3);
- sưởi (C);
- vòng nước (bài 1);
- cảm biến (4.1).

```json
{"vin": "VF000123", "date": "2026-10-13", "thermal_health": 62, "trend_30d": -9,
 "parts": {"lam_mat_pin": 71, "lam_mat_motor": 48, "dieu_hoa": 80, "suoi": 95, "vong_nuoc": 90, "cam_bien": 100},
 "risks": [{"issue": "giam_cong_suat", "eta_days": 25, "cause": "ket_nuoc_ban", "p": 0.7},
           {"issue": "sac_cham_vi_nhiet", "minutes_lost_month": 48, "cause": "thieu_gas", "p": 0.55}],
 "actions": {"customer": "Đặt lịch vệ sinh két nước trước mùa hè",
             "service": "Kiểm tra két nước, quạt két; đo áp gas",
             "engineering": null}}
```

**Gửi cho ai, khi nào:**

| Người nhận | Gửi khi | Nội dung | Chỉ số lợi ích |
|---|---|---|---|
| Khách (app) | Chắc chắn (p ≥ 0,7) **và** có việc cụ thể khách tự làm được hoặc nên đặt lịch | Giải thích ngắn + một việc cần làm (bật làm ấm pin, đặt lịch vệ sinh két…) | Phút sạc tiết kiệm, số lần xe bị giới hạn công suất |
| Xưởng | p ≥ 0,6, hoặc `eta_days` ≤ 30, hoặc lặp lại ≥ 3 lần | **Phiếu chẩn đoán trước**: bộ phận nghi ngờ, bằng chứng, việc kiểm tra theo thứ tự | Ít thay nhầm linh kiện, sửa nhanh hơn |
| Kỹ sư / chất lượng | Báo cáo tuần | Theo dòng xe, vùng, lô linh kiện; xe có điểm thấp bất thường | Phát hiện lỗi hàng loạt sớm, giảm chi phí bảo hành |

Lời giải thích cho khách và xưởng sinh tự động từ JSON bằng mẫu câu có sẵn, để không viết tay.

### 4.5 So với xe tương tự

- Mọi chỉ số (phút mất, số sự kiện / 1000 km, phần chênh) đều tính **phân vị trong nhóm xe tương tự**: dòng xe × vùng (Bắc / Trung / Nam) × tháng.
- Như vậy xe ở TP.HCM tháng 4 nóng là bình thường, còn xe ở Hà Nội tháng 12 mà nóng như vậy là bất thường.
- Nhóm quá nhỏ thì gộp tháng lân cận.

---

## 5. Dữ liệu

### 5.1 Dữ liệu thật VinFast (cần xin)

Cần một mẫu vài xe × vài tuần, gồm cả sạc nhanh, chạy đường dài / leo dốc và (nếu được) mùa đông. Dùng để:
- kiểm tần suất gửi, đơn vị, trường nào thực sự có dữ liệu;
- chỉnh mọi ngưỡng;
- huấn luyện lại M1–M4.

### 5.2 Dữ liệu giả (sinh hàng loạt)

**Mục đích:**
- dựng và kiểm tra toàn bộ quy trình;
- **đo thời gian báo sớm và tỉ lệ báo nhầm** khi lỗi phát triển dần;
- so sánh luật với ML trong điều kiện kiểm soát được.

**Không dùng dữ liệu giả để báo "độ chính xác X% trên xe thật".**

**Quy cách bộ sinh** (chi tiết: bộ phận, bộ điều khiển, cảm biến, lỗi, nhãn ở [`thiet_ke_du_lieu_gia.md`](thiet_ke_du_lieu_gia.md)):
- **Nền:** port engine mô phỏng trong [`vinfast_thermal_3d.html`](vinfast_thermal_3d.html) sang Python.
- **Quy mô:** khoảng 200 xe × 180 ngày, mẫu mỗi 10 giây.
- **Cột:** xuất đúng các cột của [`thermal_hvac_signals.csv`](thermal_hvac_signals.csv). Mô phỏng hiện xuất 279 cột, cần bổ sung 20 tín hiệu mới.
- **Khí hậu:** Hà Nội (có mùa đông) và TP.HCM.
- **Dòng xe:** 1 / 2 motor; PTC / heat pump nếu xác nhận được.
- **Cho giống đời thật** (để luật cứng không quá dễ thắng):
  - mỗi xe khác nhau ±10–20% (khả năng tản nhiệt của két, lưu lượng bơm, khối nhiệt pin);
  - nhiễu cảm biến, mất mẫu 1–5%;
  - nhiều kiểu lái, nhiều loại trạm sạc;
  - lịch trình theo ngày thường / cuối tuần.
- **Lỗi có nhãn** (`fault_type`, `onset_time`, `severity(t)`), phần lớn **phát triển dần**:

| Lỗi | Cách mô phỏng | Thấy được qua | Phục vụ |
|---|---|---|---|
| Két nước / dàn nóng bẩn dần | Khả năng tản giảm 1–3%/tuần | Motor nóng hơn kỳ vọng, rõ khi chạy chậm (M1) | B |
| Bơm motor mòn | Lưu lượng giảm dần | Motor nóng hơn kỳ vọng ở mọi tốc độ (M1) | B |
| Quạt két chết | Đột ngột, có cờ | Cờ quạt, motor nóng khi đứng | B, A |
| Rò gas chậm | Lượng gas giảm 1–5%/tháng | Dàn lạnh ấm dần (M4), làm mát pin kém dần (M3) | A, B7, bài 3 |
| Chiller đóng cặn | Hiệu suất trao đổi nhiệt giảm dần | Làm mát pin kém, dàn lạnh bình thường | A |
| Bơm pin yếu | Lưu lượng giảm dần | Nước ra–vào pin chênh lớn | A |
| Rò nước làm mát | Mức nước giảm, cờ khi dưới ngưỡng | Cờ thiếu nước, nhiệt tăng | A, B, bài 1 |
| PTC hỏng | Đột ngột, có cờ | Cabin không ấm; pin lạnh khi sạc mùa đông | C, A |
| Cửa gió trộn kẹt | Đột ngột, không cờ | Cabin không ấm, không có cờ PTC | C |
| Cảm biến lệch / đứng / trôi | Offset, stuck, drift | Chính giá trị cảm biến | 4.1 |

- **Tách tập kiểm tra:** giữ riêng một số xe và một số kiểu lỗi không dùng khi chỉnh ngưỡng / huấn luyện.

### 5.3 Dữ liệu công khai để hiệu chỉnh

Không có bộ công khai nào có telemetry hệ nhiệt kiểu VinFast kèm nhãn hỏng. Các bộ dưới đây dùng để **chỉnh cho dữ liệu giả giống thật** và **thử phương pháp trên dữ liệu thật**:

| Bộ dữ liệu | Có gì | Dùng cho |
|---|---|---|
| [Battery and Heating Data in Real Driving Cycles](https://ieee-dataport.org/open-access/battery-and-heating-data-real-driving-cycles) (BMW i3, TU München) | 72 chuyến; nhiệt ngoài trời, pin, **nhiệt cabin, công suất sưởi** (mùa đông đầy đủ) | C: tốc độ cabin ấm lên; hiệu chỉnh M5 |
| [VED](https://github.com/gsoh/VED) (Ann Arbor, Apache 2.0) | 383 xe, 1 năm; có **công suất máy nén điều hòa và sưởi**, nhiệt ngoài trời (chỉ 3 xe thuần điện) | C, điều hòa theo mùa (tham khảo) |
| [KU Leuven BEV Energy Dynamics](https://pmc.ncbi.nlm.nih.gov/articles/PMC12663375/) (2 Tesla Model Y, CC BY 4.0) | Khoảng 1 năm, mẫu 1 giây; sạc DC, **nhiệt pin max/min**, nhiệt ngoài trời, SOC | A: đường sạc theo nhiệt pin; thử M2 |
| [Đường sạc nhanh số hóa theo dòng xe](https://figshare.com/articles/dataset/Digitized_Electric_Vehicle_Fast-Charging_Profiles_by_Model_Power_vs_SOC_SOE_CSV_Format_Version_1/30570653) | Công suất theo SOC của khoảng 100 dòng xe | A: mẫu đường sạc chuẩn |
| [Lỗi pin xe điện – Tsinghua](https://www.nature.com/articles/s41467-023-41226-5) (Nature Communications 2023) | Hơn 690.000 đoạn sạc của 347 xe, 55 xe có nhãn lỗi pin | Tập phương pháp "học hành vi bình thường → phát hiện bất thường" trên dữ liệu thật có nhãn |

Bài B chưa có bộ công khai phù hợp, nên phụ thuộc dữ liệu giả cho tới khi có dữ liệu VinFast.

---

## 6. Đánh giá

| Giai đoạn | Chỉ số | Mục tiêu ban đầu (trên dữ liệu giả, chỉnh lại khi có dữ liệu thật) |
|---|---|---|
| 1 | Precision / recall phát hiện (phiên sạc bị giới hạn, sự kiện, chuyến sưởi kém); sai số `minutes_lost` | Không báo nhầm ở xe khỏe; bắt được các lỗi nặng |
| 2 | **Số ngày báo sớm** so với luật; **báo nhầm / 1000 xe-tháng**; sai số mô hình trên xe khỏe | Báo sớm hơn luật ≥ 2 tuần với lỗi phát triển dần; báo nhầm thấp hơn hoặc bằng luật |
| 3 | Đúng nguyên nhân top-1 / top-2; tỉ lệ phiếu xưởng xác nhận đúng | Top-2 đúng ở đa số lỗi có hình mẫu riêng |
| Lợi ích | Phút sạc tiết kiệm; số lần giới hạn công suất tránh được; số lần thay nhầm | Đo khi chạy thử với xưởng |

---

## 7. Lộ trình

| Giai đoạn | Việc | Xong khi |
|---|---|---|
| **0. Đã xong** | Hiểu hệ thống, bộ phận; 299 tín hiệu; chốt A/B/C; mô hình 3D + mô phỏng + hỏng hóc + luồng hoạt động; hình bộ phận | — |
| **1. Nền tảng** (~4 tuần) | Gửi bản tóm tắt mục 0 + câu hỏi mục 9 cho lead; xin mẫu dữ liệu thật · Bộ sinh dữ liệu giả hàng loạt (5.2) · Lọc cảm biến (4.1) · Baseline luật A → B → C, đầu ra JSON · Chấm điểm trên dữ liệu giả | Chạy được cả quy trình trên 200 xe giả; bảng điểm giai đoạn 1 |
| **2. Dự báo** (~6 tuần) | M1 (bài B) → M3, M2 (bài A) → M4 · So với luật: số ngày báo sớm, báo nhầm · Hiệu chỉnh bằng dữ liệu công khai (5.3) và mẫu thật | M1 báo sớm hơn luật trên lỗi phát triển dần; báo cáo so sánh |
| **3. Chẩn đoán & hành động** (~6 tuần) | Gộp bằng chứng (4.3) · Điểm sức khỏe + gợi ý (4.4) · So với xe tương tự (4.5) · **Demo "Thẻ sức khỏe xe"** trên trang 3D: chạy lỗi phát triển dần, thẻ hiện điểm giảm, "còn khoảng X ngày", nguyên nhân kèm xác suất, bộ phận nghi ngờ sáng đỏ · Thử với một xưởng, học lại từ phiếu sửa | Phiếu chẩn đoán dùng thử ở xưởng; vòng cập nhật xác suất từ kết quả sửa |

Thời gian chỉ là ước lượng, phụ thuộc vào việc có dữ liệu thật hay không.

---

## 8. Rủi ro và cách giảm

| Rủi ro | Cách giảm |
|---|---|
| Không có dữ liệu thật trong thời gian dài | Làm hết trên dữ liệu giả đã hiệu chỉnh bằng dữ liệu công khai; thiết kế để thay nguồn dữ liệu là chạy |
| Telemetry gửi thưa (chỉ theo sự kiện) | Thiết kế đặc trưng theo phiên / chuyến, không phụ thuộc mẫu dày; kiểm ngay trên mẫu thật |
| Cờ mơ hồ (PTC gió hay nước, "error level" nghĩa là gì) | Hỏi team (mục 9); đầu ra ghi "chưa phân biệt được" thay vì đoán |
| Mô hình học thuộc dữ liệu giả | Chỉ dùng ML không cần nhãn; tách xe / kiểu lỗi khi kiểm tra; không báo độ chính xác trên dữ liệu giả |
| Báo quá nhiều, khách khó chịu | Ngưỡng gửi cho khách cao (4.4); phần lớn gửi xưởng / kỹ sư |
| Thiếu tín hiệu (áp suất gas, tốc độ máy nén, vị trí van) | Ghi rõ giới hạn; đề xuất bổ sung tín hiệu vào telemetry nếu CAN có sẵn |

---

## 9. Câu hỏi cho team

1. Tần suất gửi telemetry thực tế (1 giây, 10 giây, theo sự kiện)? Nhóm `Realtime Bus Monitoring` có gửi liên tục không?
2. Cờ `PTC module failure` / `VCU Ptc component error level` là PTC gió hay PTC nước, hay xe chỉ có một bộ?
3. Dòng xe nào có heat pump, dòng nào 2 motor, dòng nào có AGS?
4. `EDS current temperature` (`34233.3.232`) là nhiệt inverter, motor hay cả cụm? `Motor Temperature` (`34233.3.231`) là motor trước hay sau?
5. Bảng mã của các trường "error level" và "pump state"?
6. CAN có áp suất gas / tốc độ máy nén / vị trí van không? Nếu có, có thể xin bổ sung vào telemetry?
7. Có lịch sử xưởng dịch vụ / claim bảo hành để làm nhãn thật không?
8. Đầu ra cuối cùng cần ở dạng nào: dashboard, cảnh báo cho xưởng, thông báo trên app, hay báo cáo định kỳ?
9. Một số telltale có hai mã (ví dụ `34200.1.68` và `34200.25.28` đều là Power limitation warning): khác dòng xe hay khác phiên bản?

---

## Phụ lục A. Hệ thống nhiệt và các bộ phận

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


### Bộ phận: vị trí, lỗi thường gặp, dấu hiệu trên telemetry

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

## Phụ lục B. Từ điển trường telemetry

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

## Phụ lục C. Các bài cũ (B5–B15) trong kiến trúc mới

| Bài cũ | Khả thi | Vị trí trong kế hoạch v2 |
|---|---|---|
| B5 Cảm biến đáng tin không | 🟡 (không có áp suất gas) | **Bước chung 4.1**, làm đầu tiên |
| B6 Sức khỏe làm mát pin | ✅ | **Mô hình M3**, phục vụ bài A và điểm sức khỏe |
| B7 Rò gas chậm | 🟡 gián tiếp (không có áp suất, tốc độ máy nén) | **Mô hình M4** (nhiệt dàn lạnh kỳ vọng); bằng chứng cho chẩn đoán 4.3 |
| B8 Giảm công suất do nhiệt | ✅ | = **Bài B** |
| B9 Sạc nhanh chậm vì nhiệt | ✅ | = **Bài A** |
| B10 Sưởi kém | 🟡 | = **Bài C** |
| B11 Năng lượng điều hòa bất thường | 🟡 (chỉ có năng lượng cộng dồn `34198.1.6`) | Để sau; cùng kiểu mô hình hành vi bình thường (dự đoán kWh điều hòa / chuyến) |
| B12 Van / EXV / cửa gió kẹt | 🔴 (không có vị trí) | Chỉ đếm cờ lỗi; là một nguyên nhân trong bảng 4.3 |
| B13 Lọc gió / blower yếu | 🔴 (không có công suất blower) | Tạm hoãn; nhắc thay lọc theo thời gian / km |
| B14 Độ tin cậy linh kiện | ⚪ cần bảo hành, lô sản xuất | Phần "kỹ sư / chất lượng" ở giai đoạn 3 (Weibull, Kaplan–Meier) |
| B15 Điểm sức khỏe tổng hợp | ✅ | **Mục 4.4** |

> Ngoài phạm vi: cảnh báo cháy nổ pin (thermal runaway) thuộc nhóm Pin.
