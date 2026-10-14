# Bài A – Cách giải hiện tại

> **Bài A:** Sạc chậm vì nhiệt → bộ phận nào đang yếu → sức khỏe bộ phận đó trong tương lai.
> Tài liệu mô tả **cách giải đang dùng** (giai đoạn 1: luật + công thức đơn giản), theo **3 câu hỏi nối tiếp**, có ví dụ số. Công thức đầy đủ và phần ML ở [`bai_A_cong_thuc_va_ML.md`](bai_A_cong_thuc_va_ML.md); phát biểu bài toán ở [plan, mục 3.A](VeHatI_Thermal_HVAC_Plan.md).
> Ngưỡng trong tài liệu là **giá trị khởi đầu**, chọn trên mô phỏng, phải chỉnh lại khi có dữ liệu thật.

---

## Bài toán theo 3 câu hỏi

```
TẦNG 1  PHÁT HIỆN   Phiên sạc này có bị chậm DO NHIỆT không?
                    → có / không · pin nóng hay lạnh · mất bao nhiêu phút
   │  không do nhiệt (trạm yếu, SOC cao…) → dừng
   ▼  do nhiệt
TẦNG 2  CHẨN ĐOÁN   Nếu do nhiệt, BỘ PHẬN NÀO đang yếu?
                    → hệ tản kém ở khâu nào → bộ phận nghi ngờ + xác suất
                    → bao nhiêu phút mất là do bộ phận đó, bao nhiêu do trời / cách dùng
   │  không bộ phận nào yếu (do điều kiện) → dừng
   ▼  có bộ phận yếu
TẦNG 3  DỰ BÁO      SỨC KHỎE bộ phận đó trong TƯƠNG LAI ra sao?
                    → điểm sức khỏe theo tuần · đang yếu đi nhanh cỡ nào
                    → còn bao lâu thì gây sạc chậm rõ rệt · mùa tới sẽ mất bao nhiêu phút mỗi lần sạc
```

| Tầng | Câu hỏi | Đơn vị phân tích | Đầu ra chính |
|---|---|---|---|
| 1. Phát hiện | Sạc chậm có do nhiệt không? | Mỗi phiên sạc | Có / không · nóng / lạnh · số phút mất |
| 2. Chẩn đoán | Bộ phận nào đang yếu? | Mỗi phiên, xác nhận qua nhiều phiên | Bộ phận nghi ngờ + xác suất · bằng chứng · phút mất do bộ phận / do điều kiện |
| 3. Dự báo | Sức khỏe bộ phận đó sắp tới ra sao? | Mỗi xe × tuần | Điểm sức khỏe · tốc độ xuống cấp · còn bao lâu · phút mất dự kiến mùa tới |

---

## Chuẩn bị dữ liệu (dùng chung)

**Tín hiệu cần dùng:**

| Nhóm | Tín hiệu | Mã | Dùng ở tầng |
|---|---|---|---|
| Tách phiên | Trạng thái sạc · loại sạc · súng sạc DC | `34193.1.5` · `34193.1.32` · `34193.1.17` | Chung |
| Kết quả sạc | Công suất sạc · dòng pack · điện áp pack | `34220.1.118` · `34220.1.59` · `34220.1.60` | 1 |
| BMS quyết định | Dòng sạc cho phép · dòng BMS yêu cầu trạm | `34220.1.106` · `34220.1.76` | 1 |
| Mức pin | SOC | `34183.1.9` | 1 |
| Nhiệt pin | Cell lớn nhất / nhỏ nhất · chênh nhiệt cell | `34220.1.80 / .78` · `34220.1.81` | 1, 2 |
| **Hệ tản** | **Nước vào / ra tấm làm mát** · yêu cầu làm mát · trạng thái bơm pin · làm ấm pin | `34220.1.104 / .105` · `34220.1.109` · `34233.8.12` · `34233.4.4` | 2, 3 |
| Môi trường | Nhiệt ngoài trời | `34183.1.7` | 1, 2, 3 |
| Dấu vết ngoài phiên sạc | Nhiệt dàn lạnh · cờ quạt, máy nén, thiếu nước, van, bơm, PTC | `34233.9.39` · `34233.2.9`, `34233.2.184`, `34200.7.1`, `34233.2.11`, `34233.2.192`, `34233.2.198` | 2 |

**Tần suất** khi đang sạc: 10 giây / mẫu (tối thiểu 30 giây), các tín hiệu cùng mốc thời gian.

**Làm sạch:**
1. Sắp xếp theo thời gian, bỏ dòng trùng.
2. Khe ≤ 30 giây thì nội suy; khe dài hơn thì đánh dấu.
3. Nhiệt độ làm mượt bằng trung vị 1 phút (thường bị làm tròn 1°C).
4. **Kiểm tra cảm biến nước vào / ra:** lúc xe đỗ nguội ≥ 6 giờ, các cảm biến nhiệt pin phải gần bằng nhau. Lệch > 3°C thì **không dùng** cảm biến đó.

**Tách phiên sạc DC:**
- Một phiên = khoảng liên tục **đang sạc + súng DC cắm + loại DC + công suất > 1 kW**.
- Gộp các khe < 2 phút; bỏ phiên < 5 phút hoặc mất > 20% dữ liệu.

---

## TẦNG 1 – Phát hiện: sạc chậm có do nhiệt không?

**Đầu vào:** công suất, dòng, điện áp sạc; dòng cho phép, dòng BMS yêu cầu; SOC; nhiệt cell lớn nhất / nhỏ nhất.

### 1.1 So với đường sạc chuẩn
Mỗi dòng xe có **đường sạc chuẩn**: ở mỗi mức SOC, xe khỏe với pin 20–35°C sạc được bao nhiêu kW. Lấy từ thông số hãng, hoặc phân vị 90 các phiên có nhiệt pin tốt.

Ví dụ: 120 kW tới 50% SOC, giảm dần còn khoảng 50 kW ở 80%.

### 1.2 Loại trừ: chậm có phải do trạm không

| Tình huống | Kết luận |
|---|---|
| Dòng thực **thấp hơn hẳn** dòng BMS yêu cầu (< 90%) | **Trạm sạc** không cấp đủ → **không do nhiệt**, dừng |
| Dòng thực ≈ dòng BMS yêu cầu, **dòng cho phép bị tụt** | **Pin bị BMS hãm** → xét tiếp |

### 1.3 Pin bị hãm vì nóng hay lạnh

| Điều kiện | Kết luận |
|---|---|
| Cell lớn nhất > **45°C** | Do nhiệt: **pin nóng** |
| Cell nhỏ nhất < **15–20°C** | Do nhiệt: **pin lạnh** |
| Nhiệt pin bình thường | **Không do nhiệt** (SOC cao, lệch cell…), dừng |

### 1.4 Luật kết luận
> **Sạc chậm do nhiệt** khi công suất thực **< 85% đường chuẩn** kéo dài **≥ 2 phút**, trong lúc **pin bị hãm vì nóng hoặc lạnh**.

### 1.5 Mất bao nhiêu phút
Trong 10 giây, nếu chỉ sạc được 75% tốc độ chuẩn thì **mất 2,5 giây**.
```
Phút mất = cộng, qua mọi mẫu bị hãm vì nhiệt, của:  10 giây × (1 − công suất thực / công suất chuẩn)
```

| Đoạn | Thời gian | Công suất thực / chuẩn | Thời gian mất |
|---|---|---|---|
| SOC 45–55%, cell 46°C | 6 phút | 75% | 1,5 phút |
| SOC 55–70%, cell 48°C | 12 phút | 60% | 4,8 phút |
| SOC 70–80%, cell 47°C | 9 phút | 70% | 2,7 phút |
| **Tổng** | | | **9 phút** |

**Đầu ra tầng 1:** `cham_do_nhiet` (có / không) · `ly_do` (pin_nong / pin_lanh / tram_sac / khac) · `phut_mat`.

---

## TẦNG 2 – Chẩn đoán: nếu do nhiệt, bộ phận nào đang yếu?

**Đầu vào:** phiên đã được tầng 1 kết luận "do nhiệt"; nhiệt nước vào / ra, yêu cầu làm mát, bơm, làm ấm, nhiệt cell, dòng sạc, nhiệt ngoài trời; dấu vết ngoài phiên (dàn lạnh cabin, các cờ lỗi).

Làm theo 3 bước: **khâu nào kém** (trong phiên) → **bộ phận nào** (thêm dấu vết) → **xác nhận** (qua nhiều phiên).

### 2.1 Khâu nào của hệ tản kém (trong phiên)

Xét các đoạn **BMS đang xin làm mát** (`34220.1.109` > 0), bỏ 5 phút đầu mỗi đoạn. Pin lạnh thì xét đoạn **đang làm ấm**.

Hình dung: pin là **nồi đang đun**, nước làm mát là **nước lạnh chảy qua đáy nồi**.

**a) Có phản ứng không?**
- Từ lúc BMS xin làm mát, nước vào pin phải **tụt ≥ 3°C trong 15 phút**.
- Không tụt, hoặc **bơm báo tắt** khi BMS đang xin → `khong_phan_ung`.

**b) Nước đưa vào có đủ lạnh không?**
```
Độ lạnh của nước = nhiệt cell lớn nhất − nhiệt nước vào
```
- Chuẩn = **trung vị độ lạnh của các phiên xe khỏe** (mô phỏng: 9,8°C). Dưới **80% chuẩn** (mô phỏng: < 7,9°C) → `nuoc_khong_du_lanh`: khâu **làm lạnh nước** yếu. (Ngưỡng cũ < 6°C quá lỏng: ca gas còn 65% có 6,9°C vẫn lọt.) Giai đoạn 2 thay "chuẩn" bằng mức đáng lẽ theo trời và nhiệt pin (ML).

**c) Nước có chảy đủ không?**
```
Độ nóng lên của nước = nước ra − nước vào          (chảy chậm thì ra gần nóng bằng pin)
ε = (nước ra − nước vào) / (nhiệt pin − nước vào)   (≈ 0,2 là tốt; gần 1 là chảy rất chậm)
```
- Độ nóng lên > 4,5°C (hoặc ε cao), kèm chênh nhiệt cell tăng → `nuoc_chay_kem`: khâu **dòng nước** yếu.
- Khâu làm lạnh yếu **không** làm ε đổi, nên b) và c) chỉ ra hai khâu khác nhau.

**d) Pin tự nóng hơn hay hệ tản yếu?**
```
Pin nóng thêm = a × (dòng sạc)²  −  k × (nhiệt pin − nước vào)
                (pin tự sinh nhiệt)   (nước kéo nhiệt đi)
```
- Dò `a`, `k` khớp nhất với dữ liệu phiên (hồi quy).
- `k` giảm → hệ tản kéo nhiệt kém.
- `a` tăng mà `k` bình thường → **pin già**, không phải hệ tản.

**e) Pin lạnh:**
- **Đã làm ấm** mà nước vào không ấm hơn cell ≥ 3°C sau 10 phút → `lam_am_kem`.
- **Không làm ấm** → `khong_lam_am_truoc` (do cách dùng, không có bộ phận yếu).

**Hệ tản ổn ở mọi câu** (phản ứng nhanh, nước đủ lạnh, chảy đủ, `k` bình thường) thì **không có bộ phận nào yếu**: phiên chậm vì **điều kiện** (trời nóng, vừa chạy xa, sạc công suất rất cao). Dừng ở đây.

### 2.2 Từ khâu kém → bộ phận nghi ngờ

Ghép khâu kém với **dấu vết ngoài phiên sạc**:

| Khâu kém (2.1) | Dấu vết thêm | Bộ phận nghi |
|---|---|---|
| Nước không đủ lạnh | Dàn lạnh cabin **cũng ấm** khi bật điều hòa | **Thiếu gas / máy nén** (có cờ máy nén → máy nén) |
| Nước không đủ lạnh | Dàn lạnh bình thường, **có cờ quạt** | **Quạt két** (lúc sạc xe đứng yên, phụ thuộc quạt) |
| Nước không đủ lạnh | Dàn lạnh bình thường, không cờ | **Chiller / van chiller** (không tách được hai cái này) |
| Nước chảy kém | **Cờ thiếu nước** | **Thiếu nước / rò / có khí** |
| Nước chảy kém | Không cờ thiếu nước | **Bơm pin yếu** |
| Nước vào **nóng bất thường ngay đầu phiên** | Cờ van | **Van 4 ngả kẹt** (nước nóng của motor lọt sang) |
| Không phản ứng | Bơm tắt khi đang cần | Điều khiển / bơm / van chiller |
| Làm ấm kém | Cờ PTC | **PTC nước** |
| `a` tăng, `k` bình thường | — | **Pin lão hóa** (chuyển nhóm Pin) |

### 2.3 Xác nhận qua nhiều phiên
- Một phiên chưa đủ chắc. Bộ phận chỉ được kết luận khi **cùng khâu kém lặp lại ≥ 3 phiên**.
- Xác suất cho từng bộ phận lấy theo cách **gộp bằng chứng** (Bayes, plan mục 4.3): bằng chứng càng nhiều và càng khớp thì xác suất càng cao.
- Có phiếu sửa chữa của xưởng thì cập nhật lại các xác suất này: hệ thống tự học.

### 2.4 Bao nhiêu phút mất là do bộ phận yếu
Tính lại phiên **giả sử hệ tản khỏe** (dùng `k` và nhiệt nước vào của xe khỏe ở cùng trời, cùng công suất):
- số phút **vẫn mất** = **do điều kiện**;
- phần còn lại = **do bộ phận yếu**.

**Đầu ra tầng 2:** `khau_kem` · `bo_phan_nghi` (bộ phận + xác suất) · `bang_chung` · `so_phien_lap_lai` · `phut_mat_do_bo_phan` · `phut_mat_do_dieu_kien`.

---

## TẦNG 3 – Dự báo: sức khỏe bộ phận đó trong tương lai

**Đầu vào:** bộ phận nghi ngờ từ tầng 2 + chỉ số của **tất cả các phiên sạc** của xe theo thời gian.

### 3.1 Mỗi bộ phận theo dõi bằng chỉ số nào

| Bộ phận | Chỉ số sức khỏe | Ý nghĩa |
|---|---|---|
| Chiller / van chiller, thiếu gas, máy nén yếu, quạt / dàn nóng bẩn | **Sức khỏe nguồn lạnh** = độ lạnh của nước (quy về cùng trời, cùng công suất) so với lúc mới | Bộ làm lạnh nước còn mạnh bao nhiêu % |
| Bơm pin, thiếu nước, có khí | **Sức khỏe dòng nước** = so ε với lúc mới | Nước còn chảy được bao nhiêu % |
| Tấm làm mát / hệ tản nói chung | **Sức khỏe hệ tản** = `k` / `k` lúc mới | Hệ tản còn kéo nhiệt được bao nhiêu % |
| Thiếu gas (bổ sung) | Dàn lạnh cabin ấm hơn mức bình thường bao nhiêu độ | Gas còn đủ không |

"**Lúc mới**" = trung vị **10 phiên đầu tiên** của chính xe đó. Xe mới chưa đủ phiên thì dùng mốc của dòng xe.

### 3.2 Đang yếu đi nhanh cỡ nào
1. Mỗi tuần tính chỉ số sức khỏe (trung vị các phiên trong tuần).
2. **Kẻ đường xu hướng** qua các tuần; dùng cách chống điểm lạ.
3. Sức khỏe **nhảy lên đột ngột** (vừa sửa / bảo dưỡng) → tính lại mốc từ đầu. **Tụt đột ngột** → hỏng đột ngột, báo ngay.

### 3.3 Còn bao lâu
**Ngưỡng nguy hiểm:** mức sức khỏe mà một phiên sạc trưa hè chuẩn (35°C, khoảng 150 kW) sẽ đẩy pin vượt 45°C, tức bắt đầu bị hãm rõ rệt.
```
Số tuần còn lại = (sức khỏe hiện tại − ngưỡng nguy hiểm) / mức giảm mỗi tuần
```

| Tuần | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Sức khỏe nguồn lạnh | 100% | 97% | 94% | 91% | 88% | 85% |

Giảm 3% / tuần, ngưỡng nguy hiểm 70% → còn khoảng **(85 − 70) / 3 = 5 tuần**. Kèm khoảng tin cậy, ví dụ 4–7 tuần.

### 3.4 Mùa tới sẽ mất bao nhiêu phút mỗi lần sạc
Lấy **sức khỏe dự kiến** của bộ phận ở tháng tới + **thời tiết điển hình** tháng đó + **thói quen sạc** của xe (giờ sạc, công suất trạm hay dùng), tính lại một phiên điển hình:
> *"Nếu không sửa, tháng 5 mỗi lần sạc trưa sẽ mất khoảng 12 phút (hiện nay 6 phút)."*

Đây là con số dễ hiểu nhất để báo khách hoặc xưởng.

### 3.5 Bộ phận nào dự báo được, bộ phận nào không

| Kiểu hỏng | Ví dụ | Dự báo được? |
|---|---|---|
| **Xuống cấp từ từ** | Chiller đóng cặn, rò gas chậm, bơm mòn, dàn nóng bẩn, rò nước chậm | **Có**: kẻ xu hướng, ra "còn bao lâu" |
| **Hỏng đột ngột** | Quạt chết, PTC cháy, van kẹt, máy nén hỏng | **Không** dự báo trước được; chỉ phát hiện ngay khi xảy ra (tầng 1–2). Ở cấp đội xe có thể ước rủi ro theo tuổi xe / lô linh kiện khi có dữ liệu bảo hành |

**Đầu ra tầng 3:** `suc_khoe` (của bộ phận nghi) · `xu_huong_moi_tuan` · `con_khoang_tuan` (kèm khoảng tin cậy) · `phut_mat_du_kien_thang_toi`.

---

## Ví dụ trọn vẹn: 3 câu hỏi cho một xe

Xe sạc lúc 13h, trời 35°C, trạm 150 kW, SOC 20 → 80%.

| Tầng | Đo / tính được | Trả lời |
|---|---|---|
| **1. Do nhiệt?** | Dòng thực ≈ dòng BMS yêu cầu (không phải trạm); dòng cho phép tụt 380 → 220 A; cell 48°C; công suất 60–75% đường chuẩn trong 27 phút | **Có, do pin nóng · mất 9 phút** |
| **2. Bộ phận nào?** | Nước vào tụt sau 3 phút (có phản ứng) · cell 47°C, nước vào 42°C → độ lạnh 5°C (**không đủ lạnh**) · ε ≈ 0,2 (chảy bình thường) · `a`, `k` bình thường · dàn lạnh cabin bình thường, không cờ · lặp lại 4 phiên gần nhất | **Chiller / van chiller (55%)**, quạt két (25%), thiếu gas (20%) · **6,5 phút do bộ phận, 2,5 phút do trời nóng** |
| **3. Tương lai?** | Sức khỏe nguồn lạnh 78%, giảm 3% / tuần, ngưỡng 70% | **Còn khoảng 3–5 tuần**; tháng tới mỗi lần sạc trưa dự kiến mất **khoảng 12 phút** |

---

## Đầu ra

```json
{"session_id": "S-88812", "vin": "VF000123", "start": "2026-04-15 13:05",
 "tang1_phat_hien": {"cham_do_nhiet": true, "ly_do": "pin_nong", "phut_mat": 9.0},
 "tang2_chan_doan": {"khau_kem": "nuoc_khong_du_lanh",
                     "bo_phan_nghi": [{"bo_phan": "chiller_hoac_van_chiller", "p": 0.55}, {"bo_phan": "quat_ket", "p": 0.25}, {"bo_phan": "thieu_gas", "p": 0.2}],
                     "bang_chung": {"phan_ung_sau_phut": 3, "do_lanh_nuoc_c": 5.0, "epsilon": 0.2, "k_so_voi_luc_moi": 0.98,
                                    "dan_lanh_cabin": "binh_thuong", "co_loi": []},
                     "so_phien_lap_lai": 4, "phut_mat_do_bo_phan": 6.5, "phut_mat_do_dieu_kien": 2.5},
 "tang3_du_bao": {"chi_so": "suc_khoe_nguon_lanh", "suc_khoe": 0.78, "xu_huong_moi_tuan": -0.03,
                  "con_khoang_tuan": [3, 5], "phut_mat_du_kien_thang_toi": 12}}
```

---

## Đã làm được gì trên mô phỏng 3D

Trang [`vinfast_thermal_3d.html`](vinfast_thermal_3d.html) → **Mô phỏng vận hành** chạy bản đơn giản, mỗi 10 giây, **chỉ đọc cột telemetry** (giải thích ở [`giai_thich_mo_phong_3d.md`](giai_thich_mo_phong_3d.md)):

| Tầng | Bộ phát hiện trong trang | Luật đang dùng | Còn thiếu |
|---|---|---|---|
| Chuẩn bị | **B5 – Cảm biến nhiệt lệch** | Đỗ nguội: nước vào lệch > 3°C; lúc chạy mà pin không trao đổi nhiệt: nước vào / ra lệch > 3,5°C | — |
| **1. Do nhiệt?** | **B9 – Sạc nhanh chậm vì nhiệt** | Công suất < 85% đường chuẩn suốt 2 phút; cell > 45°C → nóng; cell < 15°C → lạnh (có / không làm ấm) | Số phút mất; loại trừ trạm bằng dòng cho phép / dòng yêu cầu |
| **2. Bộ phận nào?** | **B6 – Làm mát pin kém** (một phần) | BMS xin làm mát 5 phút: nước ra − vào > 4,5°C → chảy kém (bơm / thiếu nước); độ lạnh < 80% mức xe khỏe → không đủ lạnh (chiller / gas / quạt). Bỏ qua nếu đang nghi cảm biến | Độ trễ phản ứng, ε, `a` / `k`; ghép dấu vết ngoài phiên; xác nhận nhiều phiên; xác suất; tách phút mất |
| **3. Tương lai?** | Chưa có | — | Toàn bộ: cần nhiều phiên × nhiều tuần, lỗi nặng dần |

**Kết quả thử** (kịch bản trưa nắng TP.HCM): bật **từng** lỗi chiller, bơm, gas, quạt thì B6 và B9 bắt được; xe khỏe không bị báo nhầm. Bật **cùng lúc** lỗi lệch cảm biến thì B6 tự bỏ qua nên **bỏ sót** (lỗi che lỗi).

---

## Giới hạn và bước tiếp theo

**Giới hạn:**
1. Không có lưu lượng nước, áp suất gas, trạng thái chiller → một số bộ phận **không tách được** (chiller với van chiller); đầu ra ghi "chưa phân biệt được".
2. Ngưỡng cứng (45°C, 80% độ lạnh xe khỏe, 4,5°C, 85%) **bị ảnh hưởng bởi thời tiết**, dễ báo nhầm vào mùa hè.
3. Cảm biến nước vào / ra sai thì tầng 2 và 3 sai. Khi nghi cảm biến nên chuyển sang chỉ số khác (so cell với nước ra) thay vì bỏ qua.
4. Bộ phận hỏng đột ngột không dự báo trước được.
5. Chưa có dữ liệu thật để chỉnh ngưỡng.

**Bước tiếp theo:**
1. Viết tầng 1 và tầng 2 thành code Python, chạy trên CSV của mô phỏng.
2. Sinh dữ liệu giả nhiều xe × nhiều tuần, có lỗi nặng dần, để làm tầng 3.
3. **Giai đoạn 2 (ML):** thay ngưỡng cứng bằng **"mức đáng lẽ phải có"** học từ xe khỏe; dùng lọc Kalman cho dự báo. Chi tiết ở [`bai_A_cong_thuc_va_ML.md`](bai_A_cong_thuc_va_ML.md), mục 6.
4. Khi có mẫu dữ liệu thật: kiểm tra tần suất, đơn vị, chỉnh ngưỡng.
