# Giải thích phần mô phỏng trong trang 3D

> Tài liệu này giải thích **trang [`vinfast_thermal_3d.html`](vinfast_thermal_3d.html) mô phỏng những gì và mô phỏng như thế nào**: mỗi giây máy tính tính gì, bộ điều khiển quyết định ra sao, lỗi giả lập tác động vào đâu, dữ liệu CSV xuất ra gồm những cột nào.
> Mô phỏng là **mô hình nhiệt đơn giản**: đúng xu hướng (sạc nhanh làm pin nóng, rò gas làm dàn lạnh ấm lên, quạt chết làm điều hòa yếu khi xe đứng…), nhưng **chưa hiệu chuẩn theo xe VinFast**. Các con số chỉ để minh họa.

---

## 1. Trang 3D có ba chế độ "chạy"

| Chế độ (nút trên thanh) | Để làm gì | Có tính vật lý không | Có xuất dữ liệu không |
|---|---|---|---|
| **Mô phỏng vận hành** | Chạy một kịch bản thật theo thời gian (lái, sạc, đỗ), có thể bơm lỗi, xem biểu đồ, xem các bài toán phát hiện lỗi, **tải CSV** | **Có**: mỗi giây tính lại nhiệt pin, cabin, motor, gas… | **Có**: CSV đủ cột tín hiệu telemetry |
| **Luồng hoạt động** | Xem **từng bước** một hoạt động diễn ra thế nào (làm mát cabin, làm mát pin khi sạc…), camera bay tới từng bộ phận, có giải thích | Không: là minh họa từng bước, số liệu là ví dụ | Không |
| **Hỏng hóc** | Xem **một lỗi trông ra sao** trên mô hình 3D theo 3 bài A/B/C, lỗi ảnh hưởng lan sang đâu, telemetry thấy được gì | Không: là minh họa | Không |

Phần lớn tài liệu này nói về **Mô phỏng vận hành** (mục 2–9). Hai chế độ còn lại ở mục 10–11.

---

## 2. Cách dùng Mô phỏng vận hành

1. Bấm **"Mô phỏng vận hành"**. Bảng mô phỏng hiện ra dưới khung 3D; các nút chế độ khác bị khóa trong lúc mô phỏng.
2. Chọn **Kịch bản** (mục 3) và **Tốc độ**:
   - ×10;
   - ×60 (1 giây thật = 1 phút mô phỏng);
   - ×300;
   - ×1200 (dùng cho kịch bản đỗ qua đêm).
3. (Tùy chọn) Mở **"Lỗi giả lập"**, tích vào lỗi muốn bơm và kéo thanh để chọn mức độ (mục 6).
4. Bấm **Chạy**. Trong lúc chạy:
   - đồng hồ hiện giờ mô phỏng, pha hiện tại (lái / sạc / đỗ), số dòng dữ liệu đã ghi;
   - **mô hình 3D sống theo dữ liệu**: ống nào đang chảy thì sáng, quạt két và blower quay theo tốc độ thật, cửa gió và lưới AGS đóng mở, bộ phận nóng / lạnh phát sáng, nhãn bộ phận hiện số đo;
   - **biểu đồ** vẽ dần 4 nhóm đại lượng (mục 8);
   - dòng **cảnh báo** hiện các đèn báo đang bật, giống đồng hồ xe;
   - bảng **bài toán phát hiện** cập nhật trạng thái từng bài (mục 7).
5. Xong (hoặc tạm dừng), bấm **"Tải dữ liệu CSV"** (mục 9).
6. **Đặt lại** để chạy lại từ đầu; đổi kịch bản cũng tự đặt lại.

---

## 3. Bốn kịch bản

| Kịch bản | Bắt đầu | Ngoài trời | Các pha | Phục vụ bài |
|---|---|---|---|---|
| **Trưa nắng TP.HCM** | 15/4, 11:30 | 35°C (dao động nhẹ), nắng 800 W/m² | Lái 35 phút (phố + đường nhanh xen kẽ) → **sạc nhanh DC 35 phút** (có bật điều hòa khi ngồi chờ) → đỗ 15 phút | **A** (pin nóng khi sạc), điều hòa kém lạnh |
| **Sáng đông Hà Nội** | 10/1, 07:00 | 10°C, tăng dần | Lái 30 phút (từ phút 15 bắt đầu **làm ấm pin** vì sắp sạc) → sạc nhanh 35 phút → đỗ 15 phút | **A** (pin lạnh), **C** (sưởi) |
| **Đỗ qua đêm → sáng lái** | 1/6, 18:00 | 27°C ± 3,5°C theo ngày đêm, nắng theo giờ | Đỗ 11 giờ (xe nguội dần) → lái phố 20 phút | Kiểm tra cảm biến lúc xe nguội (B5), hạ nhiệt cabin sau khi đỗ |
| **Leo đèo nắng nóng** | 20/5, 13:00 | 38°C, nắng 900 W/m² | Cao tốc 15 phút → **leo dốc 8% 20 phút** → phố 10 phút → đỗ 10 phút | **B** (giảm công suất vì quá nhiệt) |

Mỗi kịch bản có nhiệt độ ban đầu riêng. Ví dụ trưa nắng: cabin 52°C (vừa đỗ nắng), pin 38°C; sáng đông: mọi thứ 10°C.

---

## 4. Mỗi giây máy tính tính gì

Mô phỏng chạy **bước 1 giây**. Mỗi bước đi theo đúng thứ tự xảy ra ngoài đời:

```
① Xe đang làm gì?          → pha (lái / sạc / đỗ), tốc độ, độ dốc, công suất kéo
② CCU (điều hòa) quyết định → bật làm mát / sưởi / tắt, mức gió, lấy gió trong hay ngoài
③ BMS (pin) quyết định      → có xin làm mát không, có cần làm ấm không
④ VCU quyết định            → bơm pin, bơm motor, quạt két, van 4 ngả, giới hạn công suất
⑤ Vòng gas lạnh             → máy nén chạy mạnh bao nhiêu, chia lạnh cho dàn lạnh và chiller
⑥ PTC                       → sưởi gió cabin, sưởi nước pin
⑦ Cabin                     → nhiệt cabin thay đổi (nắng, người, gió lạnh / nóng)
⑧ Pin – điện                → dòng điện, công suất sạc (bị BMS hãm nếu nóng / lạnh), SOC
⑨ Pin – nhiệt               → nhiệt cell, nhiệt nước pin, chênh nhiệt giữa các cell
⑩ Motor / inverter / két    → nhiệt motor, inverter, nước vòng motor
⑪ Phụ                       → mức nước (nếu rò), năng lượng cộng dồn, odometer, GPS, cờ
```

**Cứ 10 giây** (giờ mô phỏng), trạng thái được **chụp lại thành một dòng dữ liệu**, giống telemetry gửi về server. Ngay sau đó các **bài toán phát hiện** chạy trên dòng mới (mục 7) và **mô hình 3D** cập nhật theo dòng đó.

---

## 5. Mô hình vật lý và bộ điều khiển

Mỗi khối nhiệt là **một nút**: `khối nhiệt × tốc độ đổi nhiệt = nhiệt vào − nhiệt ra`. Các hằng số dưới đây lấy đúng từ code, là giá trị giả định.

### 5.1 Xe và công suất kéo
```
Công suất ở bánh = lực cản lăn + lực dốc + lực gió + lực tăng tốc       (xe 2100 kg, CdA 0,72)
Công suất điện   = công suất bánh / 0,9           (phanh tái sinh thu lại 60%)
Bị giới hạn công suất → công suất kéo giảm còn 50%
```
Tốc độ theo kiểu đường:
- **phố:** chu kỳ 150 giây, tăng tốc lên 45 km/h, chạy, rồi dừng;
- **cao tốc:** khoảng 100 km/h;
- **đèo:** khoảng 70 km/h ở dốc 8%;
- **hỗn hợp:** xen kẽ phố và đường nhanh mỗi 10 phút.

### 5.2 CCU – điều hòa
- **Bật** khi có người trong xe: đang lái, hoặc đang ngồi chờ sạc.
- **Làm mát** nếu ngoài trời ≥ 18°C, **sưởi** nếu lạnh hơn. Đây là cách đơn giản hóa so với xe thật.
- **Mức gió** = 2 + |cabin − cài đặt| / 2,5, giới hạn 2–7.
- **Lấy gió trong** khi đang làm mát mà cabin còn nóng hơn cài đặt > 3°C.
- **Máy nén cho cabin:** giảm dần khi cabin gần cài đặt; giảm khi dàn lạnh xuống gần 3°C (chống đóng băng).

### 5.3 BMS – pin
- **Xin làm mát** = (cell nóng nhất − ngưỡng) × 1,2, tối đa 6 kW. Ngưỡng là **32°C khi đang sạc**, 38°C khi lái.
- **Cần làm ấm** khi cell lạnh nhất < 18°C (lúc sạc hoặc đang làm ấm trước khi sạc) và ngoài trời < 20°C.
- **Hãm sạc** theo nhiệt:
  - cell nóng nhất > 45°C → giảm dần, còn 25% ở 53°C;
  - cell lạnh nhất < 20°C → còn 15–100% tùy độ lạnh.
- **Đường sạc chuẩn** theo SOC: 120 kW tới 50%, giảm dần còn 50 kW ở 80%. Sạc tới 80% thì dừng.

### 5.4 VCU – bơm, quạt, van, giới hạn công suất
- **Bơm pin** chạy khi lái, sạc, hoặc BMS xin làm mát / làm ấm.
- **Bơm motor** chạy khi lái, sạc, hoặc nước motor > 45°C.
- **Quạt két:**
  - theo nước motor (từ 42°C, tối đa ở 57°C);
  - tối thiểu 35–60% khi máy nén chạy;
  - 80% khi xe gần như đứng yên mà máy nén chạy mạnh.
- **AGS** mở khi quạt hoặc máy nén chạy.
- **Van 4 ngả** chuyển **nối tiếp** (nước motor sang pin) khi pin cần ấm, xe đang lái và nước motor ấm hơn nước pin > 5°C.
- **Giới hạn công suất** khi motor > 130°C, inverter > 90°C hoặc cell > 52°C.

### 5.5 Vòng gas lạnh
```
Khả năng làm lạnh tối đa = 6,5 kW × hệ số gas × hệ số dàn nóng × hệ số trời nóng
  hệ số gas      : 1 khi đủ gas, giảm nhanh khi gas < ~90%, bằng 0 khi gas ≤ 45%
  hệ số dàn nóng : 0,3 + 0,7 × lượng gió qua dàn nóng
                   (gió = tốc độ xe / 80 km/h + 0,9 × quạt; xe đứng yên chỉ còn nhờ quạt)
  hệ số trời nóng: giảm khi ngoài trời > 35°C
Máy nén tăng / giảm dần tới mức cần (cabin + chiller)
Chiller lấy nhiệt nước pin = 260 W/K × hiệu suất chiller × (nước pin − 4°C) × lưu lượng
  (nếu cabin cũng đang làm mát thì chiller chỉ được tối đa 55% lạnh)
Dàn lạnh: lạnh xuống nhờ gas, ấm lên nhờ gió đi qua → ra "nhiệt dàn lạnh"
Công suất máy nén = lạnh / hiệu suất (thấp hơn khi dàn nóng thiếu gió)
```

### 5.6 PTC
- **PTC gió** = (cài đặt + 4 − cabin) × 700 W, tối đa 5 kW, khi đang sưởi.
- **PTC nước** = tối đa 5 kW, giảm dần khi nước pin gần 45°C, khi BMS cần làm ấm.

### 5.7 Cabin
```
Nhiệt vào cabin = 130 W/K × (ngoài − cabin) + 70% nắng + 120 W (người) + PTC gió − lạnh từ dàn lạnh
Khối nhiệt cabin 90 kJ/K
```

### 5.8 Pin
```
Điện áp ≈ 330 + 70 × SOC (V);  dòng = công suất / điện áp;  nhiệt sinh = dòng² × 0,06 Ω
Khối cell (350 kJ/K):  nhận nhiệt sinh ra, nhả nhiệt cho nước qua tấm làm mát (450 W/K × lưu lượng), thất thoát nhẹ ra ngoài
Nước pin (70 kJ/K):    nhận nhiệt từ cell, bị chiller lấy nhiệt, được PTC nước làm ấm, nhận nước motor nếu van nối tiếp
Chênh nhiệt cell:      tăng khi dòng lớn và lưu lượng thấp
Nước vào / ra pin:     = nhiệt nước pin ∓ một nửa độ chênh (độ chênh = nhiệt mang đi / lưu lượng) → lưu lượng thấp thì chênh lớn
```

### 5.9 Motor, inverter, két nước
```
Nhiệt sinh = 9% công suất kéo (60% ở motor, 40% ở inverter)
Motor (40 kJ/K), inverter (8 kJ/K) nhả nhiệt cho nước vòng motor (tỉ lệ lưu lượng)
Két nước thải nhiệt = 600 W/K × gió qua két × lưu lượng × (nước motor − ngoài trời)
  (van nối tiếp thì két gần như bị bỏ qua)
```

### 5.10 Rò nước và các cờ
- Rò nước làm **mức nước** giảm theo giờ. Dưới 60% thì có khí lọt vào vòng nước và **lưu lượng cả hai vòng giảm**. Dưới 70% thì bật cờ **thiếu nước làm mát**.
- Các cờ khác (pin nóng, pin lạnh, sạc lâu hơn, lỗi quạt, lỗi PTC…) bật theo ngưỡng trên trạng thái mô phỏng.

---

## 6. Lỗi giả lập

Bật trong mục **"Lỗi giả lập"**. Mỗi lỗi **đổi một tham số vật lý**, không sửa thẳng vào tín hiệu. Riêng lỗi cảm biến thì nằm ở lớp đo.

| Lỗi | Mức chỉnh | Tác động trong mô hình | Hệ quả thấy được |
|---|---|---|---|
| **Rò gas** | Gas còn 40–100% (mặc định 60%) | Giảm khả năng làm lạnh tối đa | Dàn lạnh ấm hơn; nước vào pin không đủ lạnh khi sạc |
| **Bơm pin suy giảm** | Lưu lượng còn 10–100% (mặc định 40%) | Giảm lưu lượng vòng pin | Nước ra − vào pin chênh lớn; chênh nhiệt cell tăng; pin nóng hơn khi sạc |
| **Quạt két chết** | Bật / tắt | Quạt = 0 dù có lệnh; VCU báo lỗi quạt | Xe đứng (sạc, kẹt xe) thì điều hòa và làm mát pin yếu, nước motor nóng |
| **Chiller kém** | Hiệu suất còn 10–100% (mặc định 15%) | Giảm nhiệt chiller lấy được từ nước pin | BMS xin làm mát mà nước vào pin gần bằng nhiệt cell; sạc chậm |
| **Rò nước làm mát** | 5–100% mỗi giờ (mặc định 40%) | Mức nước giảm dần | Cờ thiếu nước; lưu lượng giảm, pin và motor nóng hơn |
| **Cảm biến nước vào pin lệch** | −10…+10°C (mặc định +6°C) | Cộng thêm vào **số đo**, nhiệt thật không đổi | Cảm biến lệch khi xe đỗ nguội; dễ làm bài khác kết luận nhầm |
| **PTC hỏng** (gió và nước) | Bật / tắt | Công suất PTC = 0; báo lỗi PTC khi cần sưởi | Cabin không ấm; pin không được làm ấm, sạc mùa đông chậm |
| **Lọc gió cabin tắc** | Tắc 10–90% | Giảm lượng gió, blower tốn điện hơn | Cabin mát / ấm chậm. Telemetry không thấy trực tiếp |
| **Van 4 ngả kẹt nối vòng** | Bật / tắt | Luôn nối nước motor sang pin; két bị bỏ qua | Pin bị hâm nóng; VCU báo lỗi van |

Lỗi tính **từ lúc bật**. Bật trước khi Chạy thì có từ đầu; bật giữa chừng thì ghi nhận thời điểm. Lỗi giữ **nguyên mức độ**, không tự nặng dần (khác với thiết kế dữ liệu giả hàng loạt, xem mục 12).

---

## 7. Các bài toán phát hiện chạy kèm

Mỗi 10 giây, sau khi ghi một dòng dữ liệu, **9 bộ phát hiện** chạy trên dữ liệu vừa ghi. Bộ phát hiện **chỉ đọc cột tín hiệu telemetry, không đọc trạng thái thật**, giống thuật toán thật trên server.

| Bộ phát hiện | Luật (tóm tắt) |
|---|---|
| **1 · Rò / thiếu nước** | Cờ thiếu nước `34200.7.1` bật → phát hiện. Không có giá trị mức nước nên chỉ biết khi đã thấp |
| **B5 · Cảm biến nhiệt lệch** | Xe đỗ ≥ 6 giờ: nước vào pin lệch > 3°C so với trung vị các cảm biến pin. Khi chạy mà pin không trao đổi nhiệt: nước vào và ra lệch > 3,5°C |
| **B6 · Làm mát pin kém** | BMS xin làm mát suốt 5 phút mà: nước ra − vào > 4,5°C → nghi bơm / thiếu nước; hoặc nước vào chỉ lạnh hơn cell < 6°C → nghi chiller / gas / quạt. Bỏ qua nếu B5 đang nghi cảm biến |
| **3 · 4 · Điều hòa kém lạnh + kiểu hỏng** | Làm mát > 10 phút, cabin còn nóng hơn cài đặt ≥ 2°C mà dàn lạnh trung bình > 10°C → kém lạnh. Có cờ quạt → quạt; kém cả khi xe chạy → gas / máy nén; chỉ kém khi đứng → gas nhẹ / dàn nóng bẩn |
| **B9 · Sạc nhanh chậm vì nhiệt** (= bài A) | Công suất < 85% đường chuẩn suốt 2 phút. Cell > 45°C → pin nóng; cell < 15°C → pin lạnh (có / không làm ấm trước) |
| **B10 · Sưởi kém** (= bài C) | Sưởi > 10 phút mà cabin thấp hơn cài đặt > 5°C (kèm cờ PTC nếu có) |
| **B8 · Giảm công suất do nhiệt** (= bài B) | Cờ giới hạn công suất bật → nguyên nhân: ngoài trời > 38°C / tải nặng / hệ làm mát kém. Motor > 110°C hoặc EDS > 80°C → "nghi ngờ" |
| **B12 · Van chia nước kẹt** | Chỉ dựa vào cờ lỗi van (không có vị trí van) |
| **B13 · Lọc gió tắc** | **Không phát hiện được**: thiếu công suất / tốc độ blower (để thấy giới hạn của telemetry) |

**Chấm điểm tự động.** Vì mô phỏng biết lỗi thật, mỗi bộ phát hiện được chấm:
- **Đúng (phát hiện)**: có lỗi và đã báo, kèm *phát hiện sau bao lâu*;
- **Đúng (không báo)**: không lỗi, không báo;
- **Báo nhầm**: không có lỗi mà báo;
- **Bỏ sót**: có lỗi mà không báo;
- **Chưa đủ điều kiện**: kịch bản không tạo tình huống để kiểm tra (ví dụ không có sạc nhanh thì bài sạc chậm không kiểm tra được).

Bộ phát hiện nào đang báo thì bộ phận tương ứng trên mô hình 3D phát sáng; bấm tên bài để xem bộ phận đó.

---

## 8. Biểu đồ và hiển thị

**Bốn biểu đồ chung trục thời gian:**

| Biểu đồ | Đường |
|---|---|
| **Pin** | Cell nóng nhất, nước vào pin, nước ra pin |
| **Cabin & dàn lạnh** | Nhiệt cabin, nhiệt dàn lạnh, nhiệt cài đặt; đường nét đứt là nhiệt ngoài trời |
| **Motor & EDS** | Nhiệt motor, nhiệt EDS; nét đứt là ngoài trời |
| **Công suất** | Công suất sạc, BMS yêu cầu làm mát, công suất máy nén (đại lượng này **không có** trong telemetry, chỉ để hiểu) |

**Trên mô hình 3D:**
- Ống chảy / nghỉ theo trạng thái thật: nhánh chiller chỉ sáng khi BMS xin làm mát, nhánh dàn lạnh khi đang làm mát cabin, đường qua két tắt khi van nối tiếp…
- Quạt két, blower quay theo tốc độ; cửa gió trộn và AGS đóng mở.
- Phát sáng:
  - PTC đỏ khi sưởi;
  - chiller, dàn lạnh xanh khi làm lạnh;
  - pin đỏ khi > 40°C, xanh khi < 10°C;
  - motor / inverter đỏ khi nóng;
  - quạt sáng khi có lệnh mà không quay;
  - bình nước sáng khi thiếu nước.
- Nhãn bộ phận hiện số đo trực tiếp.

---

## 9. File CSV xuất ra

Mỗi dòng = **10 giây**. Các nhóm cột:

| Nhóm cột | Số cột | Nội dung |
|---|---|---|
| `content.<mã> <tên> [đơn vị]` | **279** | Đúng bộ tín hiệu của `thermal_hvac_signals.csv` tại thời điểm làm mô phỏng, **luôn đủ cột** như telemetry thật (danh sách nay đã lên 299; 20 tín hiệu mới chưa có trong mô phỏng) |
| `_ctx_…` | 3 | Kịch bản, pha (lái / sạc / đỗ), cấu hình dẫn động |
| `_truth_…` | 16 | **Sự thật ẩn**, telemetry thật không có: lỗi đang bật, tốc độ / công suất máy nén, lệnh và tốc độ thật của quạt, van chiller, nhiệt chiller lấy, công suất PTC gió / nước, lưu lượng nước pin, lượng gas, mức nước, nhiệt nước motor, nhiệt nước vào pin thật (trước khi cảm biến lệch), van nối tiếp, nhiệt gió ra cửa gió |
| `_det_…` | 9 | Kết quả của 9 bộ phát hiện: 0 bình thường, 1 nghi ngờ, 2 phát hiện |

**Mỗi cột tín hiệu sinh theo một trong 4 cách:**
- **vật lý:** tính từ mô hình nhiệt / điện (nhiệt độ, công suất, SOC, tốc độ…);
- **suy ra:** luật trên trạng thái mô phỏng (cờ ngưỡng, chế độ, bản trùng của cùng tín hiệu, số cộng dồn, GPS);
- **cố định:** cấu hình xe (VIN, loại pin, phiên bản…);
- **trống:** không áp dụng hoặc không có sự kiện (ví dụ lệnh từ app khi không ai bấm).

Cách mã hóa (1/0, chữ D/P, đơn vị) là **giả định**, vì từ điển không ghi.

**Dùng CSV thế nào:**
- Coi các cột `content.*` là **đầu vào** của thuật toán.
- Các cột `_truth_*` là **đáp án** để chấm điểm hoặc để hiểu vì sao tín hiệu như vậy. **Không** đưa chúng vào thuật toán.
- So cột `_det_*` với `_truth_faults` để xem luật hiện tại đúng / sai ở đâu.

---

## 10. Luồng hoạt động (minh họa từng bước)

Chọn một trong **8 hoạt động**. Mỗi hoạt động là một chuỗi bước, tự chuyển sau khoảng 7,5 giây (có Tạm dừng / Bước trước / Bước tiếp). Ở mỗi bước:
- camera bay tới **bộ phận đang làm việc**, bộ phận đó sáng lên;
- **hạt sáng chạy dọc đúng đoạn ống** đang làm việc, theo chiều chảy. Màu theo loại: gas nóng đỏ, gas lỏng cam, gas lạnh xanh, nước pin xanh ngọc, nước motor vàng, tín hiệu hồng;
- tới bước gió vào cabin thì có **hạt gió** thổi từ taplo ra sau cabin (xanh = mát, cam = ấm; lên kính khi sấy kính), và ô **nhiệt cabin** giảm / tăng dần;
- bảng dưới ghi: hiện tượng vật lý, số đo ví dụ, **tín hiệu telemetry thấy được bước đó** (ID thật) và những gì telemetry không có.

| Hoạt động | Số bước |
|---|---|
| Làm mát cabin (A/C) | 9 |
| Làm mát pin khi sạc nhanh | 8 |
| Tản nhiệt motor & inverter | 6 |
| Sưởi cabin bằng PTC (kèm chống mờ kính, sấy kính sau, sưởi ghế) | 7 |
| Làm ấm pin trước khi sạc (mùa đông) | 5 |
| Sưởi bằng heat pump (bản xứ lạnh) | 6 |
| Tận dụng nhiệt motor sưởi pin | 4 |
| Từ cảm biến tới telemetry | 4 |

Đây là **minh họa**, không chạy mô hình vật lý. Muốn thấy số liệu thay đổi thật thì dùng Mô phỏng vận hành.

---

## 11. Hỏng hóc (minh họa lỗi theo bài A/B/C)

1. Chọn **bài** (A. Sạc nhanh chậm vì nhiệt · B. Giảm công suất vì quá nhiệt · C. Sưởi kém), rồi chọn **nguyên nhân**:
   - A: chiller, gas, máy nén, quạt két, bơm pin, van 4 ngả, PTC nước;
   - B: két nước bẩn, quạt két, bơm motor, rò nước, van 4 ngả;
   - C: PTC gió, cửa gió trộn, lọc gió.
2. Mô hình chuyển sang hình ảnh của lỗi:
   - dấu **!** đỏ trên bộ phận hỏng;
   - bộ phận đổi màu / ngừng quay / rung;
   - dòng chảy bị ảnh hưởng chậm lại;
   - bộ phận bị kéo theo sáng nóng / lạnh;
   - rò nước có giọt nước và vũng dưới gầm; rò gas có khói.
3. Thẻ thông tin ghi: **khách hàng gặp gì**, **hỏng gì**, **ảnh hưởng lan sang đâu**, **tín hiệu telemetry** thấy được, **bài toán phát hiện thế nào**, kèm ví dụ JSON đầu ra.

---

## 12. Giới hạn của mô phỏng hiện tại

| Giới hạn | Hệ quả | Hướng mở rộng (xem [`thiet_ke_du_lieu_gia.md`](thiet_ke_du_lieu_gia.md)) |
|---|---|---|
| **Một xe, một kịch bản ngắn** (vài chục phút tới 11 giờ) | Không có xu hướng theo tuần / tháng | Sinh cả đội xe × 180 ngày, lịch trình và thời tiết theo ngày |
| **Lỗi giữ nguyên mức độ** | Không thử được dự báo "còn bao lâu" | Lỗi phát triển dần (`onset`, `severity(t)`) |
| **Chưa có nhiễu, độ trễ, làm tròn của cảm biến**; không mất gói tin | Dữ liệu "sạch" hơn thật, luật cứng dễ đúng hơn thật | Thêm lớp cảm biến và lớp telemetry |
| **Mọi xe giống hệt nhau** | Không thấy khác biệt giữa các xe | Mỗi xe một bộ tham số lệch ±10–20% |
| Chế độ điều hòa chọn theo nhiệt ngoài trời; một vùng điều hòa | Đơn giản hơn xe thật | Luật CCU đầy đủ hơn, 2 vùng |
| Ngưỡng, hằng số **chưa hiệu chuẩn** | Con số chỉ để minh họa | Hiệu chỉnh bằng dữ liệu công khai, rồi dữ liệu thật |
| Xuất 279 cột (danh sách nay 299) | Thiếu 20 tín hiệu mới | Bổ sung khi port sang Python |

**Tóm lại:** Mô phỏng vận hành dùng tốt để **hiểu hệ thống chạy thế nào**, **thấy một lỗi làm tín hiệu thay đổi ra sao**, và **thử nhanh luật phát hiện** trên một tình huống. Để đánh giá thuật toán và dự báo nghiêm túc thì cần bộ sinh dữ liệu hàng loạt theo [`thiet_ke_du_lieu_gia.md`](thiet_ke_du_lieu_gia.md).
