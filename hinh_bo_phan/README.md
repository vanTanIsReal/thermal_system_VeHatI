# Hình các bộ phận hệ thống nhiệt

Hình minh họa kỹ thuật chung, **không theo bản vẽ VinFast**. Mỗi hình gồm: hình vẽ có chú thích từng chi tiết, và khung bên phải ghi chức năng, lỗi hay gặp, tín hiệu telemetry liên quan (theo `resource_dictionary_full.csv`).

- `*.svg`: bản gốc, phóng to không vỡ nét, mở được bằng trình duyệt hoặc chèn vào tài liệu.
- `png/*.png`: bản ảnh 1440×960 để chèn vào Word / PowerPoint.
- [3d_bo_phan.html](3d_bo_phan.html): thư viện mô hình 3D tương tác cho 26 mục; kéo để xoay, cuộn để phóng to, chọn **Tải ảnh PNG** để lưu hình đang xem. Cần kết nối Internet để tải Three.js.
- `png_3d/*.png`: ảnh 760×588 chụp từ `3d_bo_phan.html` (nền studio, camera căn vừa từng bộ phận), cùng tên với file SVG. Đây là hình hiện trong thẻ khi rê chuột vào bộ phận ở `../vinfast_thermal_3d.html` (đã nhúng sẵn vào file đó).
- `tao_hinh.py`: script sinh lại toàn bộ hình (`python tao_hinh.py`), sửa nội dung chữ trong file này.

| # | Bộ phận | SVG | PNG |
|---|---|---|---|
| 00 | Sơ đồ tổng thể hệ thống nhiệt | [00_so_do_tong_the.svg](00_so_do_tong_the.svg) | [png](png/00_so_do_tong_the.png) |
| 01 | Máy nén điện (EAC) | [01_may_nen_dien.svg](01_may_nen_dien.svg) | [png](png/01_may_nen_dien.png) |
| 02 | Dàn nóng (condenser) | [02_dan_nong.svg](02_dan_nong.svg) | [png](png/02_dan_nong.png) |
| 03 | Quạt két | [03_quat_ket.svg](03_quat_ket.svg) | [png](png/03_quat_ket.png) |
| 04 | Két nước (radiator) | [04_ket_nuoc.svg](04_ket_nuoc.svg) | [png](png/04_ket_nuoc.png) |
| 05 | Lưới tản nhiệt chủ động (AGS) | [05_luoi_tan_nhiet_ags.svg](05_luoi_tan_nhiet_ags.svg) | [png](png/05_luoi_tan_nhiet_ags.png) |
| 06 | Van tiết lưu điện tử (EXV) | [06_van_tiet_luu_exv.svg](06_van_tiet_luu_exv.svg) | [png](png/06_van_tiet_luu_exv.png) |
| 07 | Chiller | [07_chiller.svg](07_chiller.svg) | [png](png/07_chiller.png) |
| 08 | Dàn lạnh (evaporator) | [08_dan_lanh.svg](08_dan_lanh.svg) | [png](png/08_dan_lanh.png) |
| 09 | Bơm nước điện | [09_bom_nuoc.svg](09_bom_nuoc.svg) | [png](png/09_bom_nuoc.png) |
| 10 | Sưởi PTC nước (vòng pin) | [10_ptc_nuoc.svg](10_ptc_nuoc.svg) | [png](png/10_ptc_nuoc.png) |
| 11 | Sưởi PTC gió | [11_ptc_gio.svg](11_ptc_gio.svg) | [png](png/11_ptc_gio.png) |
| 12 | Bình nước phụ + cảm biến mức | [12_binh_nuoc_phu.svg](12_binh_nuoc_phu.svg) | [png](png/12_binh_nuoc_phu.png) |
| 13 | Van chia nước nhiều ngả | [13_van_chia_nuoc.svg](13_van_chia_nuoc.svg) | [png](png/13_van_chia_nuoc.png) |
| 14 | Pin cao áp + tấm làm mát | [14_pin_tam_lam_mat.svg](14_pin_tam_lam_mat.svg) | [png](png/14_pin_tam_lam_mat.png) |
| 15 | Motor kéo + áo nước | [15_motor_ao_nuoc.svg](15_motor_ao_nuoc.svg) | [png](png/15_motor_ao_nuoc.png) |
| 16 | Biến tần (inverter / EDS) | [16_inverter_eds.svg](16_inverter_eds.svg) | [png](png/16_inverter_eds.png) |
| 17 | Bộ sạc OBC + DC-DC | [17_obc_dcdc.svg](17_obc_dcdc.svg) | [png](png/17_obc_dcdc.png) |
| 18 | Quạt gió cabin (blower) | [18_quat_gio_blower.svg](18_quat_gio_blower.svg) | [png](png/18_quat_gio_blower.png) |
| 19 | Lọc gió cabin | [19_loc_gio_cabin.svg](19_loc_gio_cabin.svg) | [png](png/19_loc_gio_cabin.png) |
| 20 | Hộp HVAC – các cửa gió (mặt cắt) | [20_hop_hvac_cua_gio.svg](20_hop_hvac_cua_gio.svg) | [png](png/20_hop_hvac_cua_gio.png) |
| 21 | Cảm biến nhiệt (NTC) | [21_cam_bien_nhiet.svg](21_cam_bien_nhiet.svg) | [png](png/21_cam_bien_nhiet.png) |
| 22 | Cảm biến áp suất gas | [22_cam_bien_ap_suat.svg](22_cam_bien_ap_suat.svg) | [png](png/22_cam_bien_ap_suat.png) |
| 23 | Ống, kẹp ống, đầu nối &amp; O-ring | [23_ong_kep_oring.svg](23_ong_kep_oring.svg) | [png](png/23_ong_kep_oring.png) |
| 24 | BDU – hộp ngắt cao áp | [24_bdu.svg](24_bdu.svg) | [png](png/24_bdu.png) |
| 25 | Bộ điều khiển &amp; đường dữ liệu | [25_bo_dieu_khien.svg](25_bo_dieu_khien.svg) | [png](png/25_bo_dieu_khien.png) |

## Xem nhanh

![Sơ đồ tổng thể hệ thống nhiệt](png/00_so_do_tong_the.png)
![Máy nén điện (EAC)](png/01_may_nen_dien.png)
![Dàn nóng (condenser)](png/02_dan_nong.png)
![Quạt két](png/03_quat_ket.png)
![Két nước (radiator)](png/04_ket_nuoc.png)
![Lưới tản nhiệt chủ động (AGS)](png/05_luoi_tan_nhiet_ags.png)
![Van tiết lưu điện tử (EXV)](png/06_van_tiet_luu_exv.png)
![Chiller](png/07_chiller.png)
![Dàn lạnh (evaporator)](png/08_dan_lanh.png)
![Bơm nước điện](png/09_bom_nuoc.png)
![Sưởi PTC nước (vòng pin)](png/10_ptc_nuoc.png)
![Sưởi PTC gió](png/11_ptc_gio.png)
![Bình nước phụ + cảm biến mức](png/12_binh_nuoc_phu.png)
![Van chia nước nhiều ngả](png/13_van_chia_nuoc.png)
![Pin cao áp + tấm làm mát](png/14_pin_tam_lam_mat.png)
![Motor kéo + áo nước](png/15_motor_ao_nuoc.png)
![Biến tần (inverter / EDS)](png/16_inverter_eds.png)
![Bộ sạc OBC + DC-DC](png/17_obc_dcdc.png)
![Quạt gió cabin (blower)](png/18_quat_gio_blower.png)
![Lọc gió cabin](png/19_loc_gio_cabin.png)
![Hộp HVAC – các cửa gió (mặt cắt)](png/20_hop_hvac_cua_gio.png)
![Cảm biến nhiệt (NTC)](png/21_cam_bien_nhiet.png)
![Cảm biến áp suất gas](png/22_cam_bien_ap_suat.png)
![Ống, kẹp ống, đầu nối &amp; O-ring](png/23_ong_kep_oring.png)
![BDU – hộp ngắt cao áp](png/24_bdu.png)
![Bộ điều khiển &amp; đường dữ liệu](png/25_bo_dieu_khien.png)
