# Hệ thống nhiệt xe điện VinFast – VeHatI

Phân tích telemetry nhóm Nhiệt & Điều hòa. Trọng tâm: **bài toán A – sạc nhanh bị chậm do nhiệt → bộ phận làm mát pin nào đang yếu → dự báo sức khỏe bộ phận đó**.

Số liệu chạy trên dữ liệu mô phỏng, chưa hiệu chuẩn theo xe thật.

## Nội dung

| Đường dẫn | Nội dung |
|---|---|
| `BAO_CAO_VeHatI_Nhiet.md` | Báo cáo tổng hợp: giải bài A chi tiết, các bài khác nêu input / output |
| `VeHatI_Thermal_HVAC_Plan.md` | Kế hoạch v2 (bản cũ: `VeHatI_Thermal_HVAC_Plan_v1.md`) |
| `bai_A_cach_giai.md`, `bai_A_cong_thuc_va_ML.md` | Cách giải, công thức, hướng ML của bài A |
| `giai_thich_mo_phong_3d.md`, `thiet_ke_du_lieu_gia.md` | Mô hình mô phỏng; thiết kế dữ liệu giả |
| `vinfast_thermal_3d.html` | Trang 3D chạy trực tiếp trên trình duyệt: mô phỏng vận hành, hỏng hóc, luồng hoạt động, bài A |
| `mo_phong_bai_A/` | Sinh dữ liệu mô phỏng và chương trình giải bài A |
| `hinh_bo_phan/` | Hình các bộ phận hệ thống nhiệt |

## Chạy lại bài A

```
cd mo_phong_bai_A
node sinh_du_lieu.js       # → data/*.csv (53 phiên)
python giai_bai_A.py       # → ket_qua.json, biểu đồ .svg   (cần numpy, pandas)
python xuat_cho_web.py     # → bai_A_web.json
```

## Ghi công

Vỏ xe 3D: "Vinfast VF9 model (no interior)" của Giang Trần trên Sketchfab, giấy phép CC BY 4.0, đã giảm lưới (`vinfast_vf9_lite.glb`).
