# Bài A – Chạy thử trên dữ liệu mô phỏng

> Thử cách giải bài A ([`bai_A_cach_giai.md`](../bai_A_cach_giai.md)) trên dữ liệu sinh bằng **đúng engine mô phỏng của trang 3D**.
> Chương trình giải **chỉ đọc cột telemetry** (`content.*`), giống thuật toán thật trên server. Lỗi thật (cột `_truth_*`) chỉ dùng để chấm điểm.
> Số liệu là của mô phỏng, **chưa hiệu chuẩn theo xe VinFast**: dùng để thấy cách giải chạy thế nào và đo được gì, không phải độ chính xác trên xe thật.

---

## 1. Cách chạy lại

```
node sinh_du_lieu.js      → data/*.csv      (53 phiên, 10 giây / dòng, đủ cột telemetry + cột sự thật)
python giai_bai_A.py      → ket_qua.json, ket_qua_in_ra.txt, 3 biểu đồ .svg
python xuat_cho_web.py    → bai_A_web.json   (nhúng vào trang 3D, chế độ "Bài A: sức khỏe & dự báo")
```
Cần Node và Python (numpy, pandas). Engine mô phỏng nằm sẵn trong `engine/`.

## 2. Dữ liệu đã sinh

| Nhóm | Số phiên | Dùng cho |
|---|---|---|
| **Các ca lỗi riêng lẻ** trong "phiên chuẩn nặng": trưa 36°C, xe vừa chạy xa (pin đã ấm), sạc ~19 → 80%. Gồm: khỏe · chiller 50% · chiller 15% · bơm pin 40% · gas 65% · quạt két chết · van 4 ngả kẹt · cảm biến nước vào lệch +6°C. Thêm 2 phiên mùa đông Hà Nội: khỏe · PTC hỏng | 10 | Tầng 1, tầng 2 |
| **Xe khỏe**: thời tiết 30–39°C, nhiệt pin đầu phiên và SOC ngẫu nhiên | 20 | Học "mức đáng lẽ phải có" |
| **Một xe bị rò gas chậm**: gas thật 100% → 56% (giảm 4% / tuần), mỗi tuần một phiên sạc trưa, thời tiết và cách dùng thay đổi | 12 | Tầng 3 |
| **Phiên chuẩn nặng với gas giảm dần** 100% → 50% | 11 | Tìm ngưỡng nguy hiểm |

---

## 3. Học "mức đáng lẽ phải có" từ 20 phiên xe khỏe

Độ lạnh của nước (cell lớn nhất − nước vào) phụ thuộc thời tiết và nhiệt pin lúc bắt đầu sạc. Hồi quy tuyến tính trên 20 phiên khỏe cho:
```
Độ lạnh đáng lẽ = 14,30 + 0,137 × T_ngoài − 0,248 × T_cell_đầu_phiên      (sai số chuẩn của hồi quy trên 20 phiên mô phỏng: 0,39°C)
```
Các mốc khác của xe khỏe: nước ra − vào khoảng **3,1°C**; hệ số tản `k` khoảng **0,081 / phút**.

Đây là bản "ML nhẹ" của bước 1 trong phần dự báo sức khỏe: so mỗi phiên với **xe khỏe ở đúng điều kiện đó**, thay vì một ngưỡng cố định.

---

## 4. Tầng 1 + 2: sạc chậm có do nhiệt không, bộ phận nào yếu

| Ca (lỗi thật) | Chậm do nhiệt? | Phút mất | Cell đỉnh | Sức khỏe nguồn lạnh | Sức khỏe dòng nước (k) | Nước ra − vào | Dàn lạnh cabin | **Khâu kém** | **Bộ phận nghi #1** | Đúng? |
|---|---|---|---|---|---|---|---|---|---|---|
| Khỏe | Không | 0,9 | 46,2°C | 1,00 | 1,00 | 3,2°C | 2,8°C | bình thường | — | ✅ |
| Chiller 50% | Không | 0,9 | 46,2°C | 1,00 | 1,00 | 3,2°C | 2,8°C | bình thường | — | ⚠️ (xem 6.1) |
| Chiller 15% | **Có** | **4,0** | 47,6°C | **0,65** | 1,00 | 1,9°C | 0,4°C (tốt) | **nước không đủ lạnh** | **chiller / van chiller** (0,6) | ✅ |
| Gas 65% | **Có** | **3,3** | 47,4°C | **0,69** | 1,00 | 2,0°C | **22,4°C (ấm)** | **nước không đủ lạnh** | **thiếu gas** (0,65) | ✅ |
| Quạt két chết | **Có** | **4,5** | 47,7°C | **0,53** | 1,01 | 1,4°C | **24,6°C (ấm)** | **nước không đủ lạnh** | **quạt két** (0,7, có cờ quạt) | ✅ |
| Bơm pin 40% | **Có** | **2,0** | 47,1°C | 1,98 | **0,43** | **7,6°C** | 2,8°C | **nước chảy kém** | **bơm pin** (0,7) | ✅ |
| Van 4 ngả kẹt | **Có** | 1,8 | 46,9°C | 0,99 | 1,01 | 3,2°C | 2,8°C | bình thường | **van 4 ngả** (0,5, có cờ van) | ✅ |
| Cảm biến nước vào +6°C | Không | 0,9 | 46,2°C | (vô nghĩa) | (vô nghĩa) | **−2,8°C** | 2,8°C | **cảm biến nghi sai** | **cảm biến nước vào** (0,8) | ✅ |
| Hà Nội, khỏe | Không | 0,1 | — | — | 1,01 | — | — | bình thường | — | ✅ |
| Hà Nội, PTC hỏng | **Có, pin lạnh** | **7,4** | cell lạnh nhất 18,8°C | — | 1,06 | — | — | **làm ấm kém** | **PTC nước** (0,8) | ✅ |

**Đọc bảng thế nào:**
- **Tầng 1** loại đúng các ca không đáng kể (xe khỏe, cảm biến lệch) và bắt các ca bị hãm. Riêng **xe khỏe vẫn mất 0,9 phút** vì trời 36°C + pin đã ấm: đây là phần **do điều kiện**.
- **Tầng 2 tách được 3 khâu khác nhau:**
  - **Nước không đủ lạnh** (chiller, gas, quạt): sức khỏe nguồn lạnh tụt còn 0,53–0,69, còn `k` vẫn ≈ 1.
  - **Nước chảy kém** (bơm): `k` tụt còn 0,43 và nước ra − vào tăng gấp đôi (7,6°C), còn nguồn lạnh không yếu (nước vào thậm chí lạnh hơn vì chảy chậm qua chiller).
  - **Cảm biến sai:** nước vào **cao hơn** nước ra trong lúc đang làm mát là vô lý, nên bị chặn trước khi kết luận.
- **Dấu vết ngoài phiên tách tiếp:**
  - dàn lạnh cabin **ấm** (22–25°C) → vòng gas chung bị yếu: **thiếu gas** hoặc **quạt** (có cờ quạt thì là quạt);
  - dàn lạnh **bình thường** → chỉ nhánh pin yếu: **chiller / van chiller**.
- **Hệ số `a` (pin tự sinh nhiệt) giữ nguyên ≈ 10,3 ở mọi ca**, nên không ca nào bị đổ nhầm là "pin già".

![Công suất sạc](bd1_cong_suat_sac.svg)

*Gas còn 65%: công suất bắt đầu tụt sớm hơn xe khỏe khoảng 2 phút và thấp hơn suốt phần còn lại, mất 3,3 phút so với 0,9 phút của xe khỏe.*

![Nhiệt pin và nước vào](bd2_nhiet_pin_va_nuoc_vao.svg)

*Nét liền là nhiệt cell, nét đứt là nước vào pin. Xe khỏe: nước vào xuống ~32°C, cell vượt 45°C một chút. Gas 65%: nước vào chỉ xuống ~35°C rồi ấm dần lên 41°C (nguồn lạnh không đủ), cell lên 47,4°C và ở trên 45°C lâu hơn, nên BMS hãm lâu hơn.*

---

## 5. Tầng 3: dự báo sức khỏe, xe bị rò gas chậm

### 5.1 Ngưỡng nguy hiểm, tìm bằng mô phỏng
Chạy phiên chuẩn nặng với lượng gas giảm dần:

| Gas thật | 100% | 90% | 80% | 70% | 65% | 60% | 55% | 50% |
|---|---|---|---|---|---|---|---|---|
| Sức khỏe nguồn lạnh đo được | 1,00 | 1,00 | 0,90 | 0,76 | 0,69 | 0,60 | 0,51 | 0,42 |
| Phút mất | 0,9 | 0,9 | 1,5 | 2,6 | 3,3 | 4,2 | 5,3 | 8,1 |

Chọn mốc "**mất trên 5 phút** ở phiên chuẩn nặng" → **ngưỡng nguy hiểm: sức khỏe 0,54** (tương ứng gas thật ~56%). Với tốc độ rò 4% / tuần, xe **thực tế chạm ngưỡng ở tuần 11,9**.

### 5.2 Sức khỏe đo được mỗi tuần

| Tuần | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gas thật | 100% | 96% | 92% | 88% | 84% | 80% | 76% | 72% | 68% | 64% | 60% | 56% |
| Trời | 34,9 | 34,3 | 38,1 | 36,0 | 38,6 | 34,4 | 34,9 | 38,2 | 33,4 | 33,4 | 36,7 | 36,5 |
| Sức khỏe | 1,03 | 1,02 | 0,98 | 1,02 | 0,90 | 0,97 | 0,90 | 0,76 | 0,81 | 0,75 | 0,60 | 0,54 |
| Phút mất | 0,6 | 0,7 | 0,8 | 0,6 | 1,2 | 1,3 | 1,1 | 2,3 | 2,8 | 3,2 | 4,3 | 3,7 |
| Tầng 2 kết luận | — | — | — | — | — | — | — | thiếu gas | — | thiếu gas | thiếu gas | thiếu gas |

- Nhờ so với "mức đáng lẽ", tuần 3 và 5 nóng tới 38°C mà sức khỏe **không bị tụt giả**.
- Tuần 9 kết luận nhảy về "bình thường" (sức khỏe 0,81, sát ngưỡng 0,8). Đây là lý do tầng 2 cần **"lặp lại ≥ 3 phiên"** mới kết luận chắc.

### 5.3 Dự báo, kiểm tra bằng cách "tua lại thời gian"
Đứng ở từng tuần, **chỉ dùng dữ liệu tới tuần đó**, dự báo tuần chạm ngưỡng. Thực tế là **tuần 11,9**.

| Đứng ở tuần | Cách 1: xu hướng mọi tuần | Cách 2: xu hướng 5 tuần gần nhất |
|---|---|---|
| 6 | tuần 40,7 (khoảng 15–137) | tuần 27,9 |
| 7 | tuần 23,9 (16–42) | tuần 23,2 |
| **8** | tuần 18,7 (13–28) | **tuần 12,7** |
| 9 | tuần 18,4 (14–23) | tuần 15,0 |
| 10 | tuần 16,8 (14–21) | tuần 14,0 |
| 11 | tuần 14,1 (13–19) | tuần 13,4 |

![Sức khỏe theo tuần](bd3_suc_khoe_theo_tuan.svg)

**Đọc kết quả:**
- **Rò gas làm sức khỏe giảm nhanh dần:** gần như không đổi ở 4 tuần đầu, rồi tụt nhanh. Đường thẳng kẻ qua **mọi tuần** bị thoải nên **dự báo trễ** (đứng ở tuần 8 đoán tuần 18,7).
- Đường kẻ qua **5 tuần gần nhất** bắt được đoạn đang tụt nhanh: đứng ở tuần 8 đoán **tuần 12,7**, sai **chưa tới 1 tuần**, tức **báo trước khoảng 4 tuần**.
- Trước tuần 7 dữ liệu chưa đủ: khoảng tin cậy rất rộng (15–137 tuần). Đúng ra lúc này hệ thống nên nói **"chưa đủ dữ liệu để dự báo"**.
- **Bài học cho thiết kế:**
  - dùng mô hình **ưu tiên dữ liệu gần đây**, ví dụ lọc Kalman hoặc cửa sổ trượt;
  - hoặc dùng **dạng đường cong học từ đội xe** (xe khác từng rò gas thì sức khỏe tụt theo dạng nào).

---

## 6. Những gì chạy thử này cho thấy

### 6.1 Điều chỉnh / phát hiện về mô phỏng
1. **Chiller 50% không có hiệu ứng:** trong mô phỏng, chiller dư công suất, máy nén mới là giới hạn. Chiller chỉ lộ ra khi rất yếu (15%). Ngoài đời chưa chắc vậy, nên chiller yếu vừa phải có thể **không phát hiện được** nếu xe thật cũng dư công suất. Cần hỏi kỹ sư nhiệt.
2. **Phiên sạc "nhẹ" thì không lộ lỗi:** sạc 36 → 80% chỉ khoảng 20 phút, pin chỉ chạm 45–46°C ở cuối nên gần như không bị hãm. Lỗi chỉ lộ rõ trong **phiên nặng** (trời nóng, pin đã ấm, sạc từ SOC thấp). Vì vậy tầng 3 nên **ưu tiên các phiên nặng** khi đo sức khỏe.
3. **Mô phỏng không có trạm sạc yếu** (dòng BMS yêu cầu luôn được cấp đủ), nên phần "loại trừ do trạm" ở tầng 1 **chưa được thử**.
4. **Chỉ số ε (hiệu suất tấm làm mát) không dùng được trên mô phỏng này**, vì mô phỏng không mô tả bộ trao đổi nhiệt theo kiểu đó. Thay bằng **`k` và nước ra − vào**, vẫn tách được "nước chảy kém".

### 6.2 Sửa trong cách tính so với tài liệu
- **Đạo hàm nhiệt pin** phải tính **trong phiên sạc** (không lấn sang đoạn lái xe trước đó). Nếu không, hồi quy ra `k` sai hẳn.
- **Cân bằng nhiệt** dùng **nhiệt trung bình của nước** ((vào + ra) / 2) thay vì chỉ nước vào: khớp vật lý hơn (`k` ước lượng 0,081 so với thật 0,077).
- **Phút mất** phải tính mọi lúc BMS hãm vì nhiệt, không chỉ khi hãm dưới 90%.

### 6.3 Chưa làm trong lần chạy này
- Nhiễu, làm tròn 1°C, mất gói tin của cảm biến (mô phỏng hiện "sạch" hơn thật).
- Nhiều xe khác nhau một chút; xác suất bộ phận theo Bayes đầy đủ; dự báo phút mất theo mùa.

Các phần này cần bộ sinh dữ liệu hàng loạt theo [`thiet_ke_du_lieu_gia.md`](../thiet_ke_du_lieu_gia.md).
