# 📚 CHỈ MỤC TÀI LIỆU - DIGITAL TWIN PC MONITORING SYSTEM

## 📖 HƯỚNG DẪN ĐỌC TÀI LIỆU

### 🚀 Cho người mới bắt đầu (Đọc theo thứ tự)

1. **[TOM_TAT.md](TOM_TAT.md)** ⭐ BẮT ĐẦU TỪ ĐÂY
   - Tóm tắt toàn bộ hệ thống
   - Hiểu nhanh kiến trúc và luồng dữ liệu
   - 10-15 phút đọc

2. **[QUICKSTART.md](QUICKSTART.md)** 
   - Hướng dẫn nhanh bằng tiếng Việt
   - Cách chạy hệ thống từng bước
   - Troubleshooting cơ bản
   - 15-20 phút đọc

3. **[HUONG_DAN_DAY_DU.md](HUONG_DAN_DAY_DU.md)** ⭐ CHO VIẾT TÀI LIỆU
   - Giải thích chi tiết từng file
   - Giải thích từng function
   - Cấu trúc dữ liệu MongoDB
   - Ví dụ code và queries
   - 30-45 phút đọc

### 📊 Cho người đã hiểu cơ bản

4. **[DOCUMENTATION.md](DOCUMENTATION.md)**
   - Kiến trúc hệ thống chi tiết
   - Luồng dữ liệu đầy đủ
   - Cấu trúc AAS Models
   - Giải thích các thay đổi cấu hình

### 🔧 Tài liệu kỹ thuật

5. **[README.md](README.md)** (English)
   - Technical overview
   - Architecture diagram
   - Dependencies
   - API references

6. **[FIX_MONGODB_CONNECTION.md](FIX_MONGODB_CONNECTION.md)** ⚠️ QUAN TRỌNG
   - Sửa lỗi connection string
   - URL encoding cho password
   - Best practices

---

## 📁 CẤU TRÚC FILES

### 🐳 Docker & Configuration
```
docker-compose.yml      # Cấu hình BaSyx containers
                        # ✅ Đã thêm MongoDB Atlas connection

.env.example            # Template environment variables
```

### 🐍 Python Scripts

#### Core Scripts (Chạy chính)
```
pc_monitor.py          # Thu thập dữ liệu PC thật
                       # Gửi qua MQTT mỗi 5 giây
                       # ✅ Detect online/offline

databridge.py          # Cầu nối MQTT ↔ MongoDB ↔ AAS
                       # ✅ Lưu telemetry
                       # ✅ Track status changes
                       # ✅ Create events/alerts
                       # ✅ Update AAS models
```

#### Utility Scripts
```
start_system.py        # Khởi động tự động
stop_system.py         # Dừng hệ thống
check_system.py        # Health check tất cả services
pc_simulator.py        # Simulator để test (không dùng psutil)
```

### 📂 Directories
```
databridge/            # Config files cho Data Bridge
├── mqttconfig.json    # MQTT datasource config
├── aasconfig.json     # AAS sink config
└── routes.json        # Data routing rules

.venv/                 # Python virtual environment
```

---

## 🎯 USE CASES - ĐỌC FILE NÀO?

### "Tôi muốn hiểu hệ thống nhanh nhất"
→ Đọc: **TOM_TAT.md** (5-10 phút)

### "Tôi muốn chạy thử hệ thống"
→ Đọc: **QUICKSTART.md** → Làm theo từng bước

### "Tôi cần viết tài liệu/báo cáo"
→ Đọc: **HUONG_DAN_DAY_DU.md** + **DOCUMENTATION.md**

### "Tôi gặp lỗi kết nối MongoDB"
→ Đọc: **FIX_MONGODB_CONNECTION.md**

### "Tôi muốn hiểu code chi tiết"
→ Mở files: `databridge.py`, `pc_monitor.py` → Đọc comments trong code

### "Tôi muốn customize hệ thống"
→ Đọc: **DOCUMENTATION.md** → Section "PHẦN 7: CODE SCRIPTS CHI TIẾT"

---

## 📊 BẢNG SO SÁNH FILES

| File | Nội dung | Độ chi tiết | Đối tượng |
|------|----------|-------------|-----------|
| TOM_TAT.md | Tóm tắt tổng quan | ⭐ Vừa phải | Người mới, người cần hiểu nhanh |
| QUICKSTART.md | Hướng dẫn nhanh | ⭐⭐ Chi tiết | Người muốn chạy thử |
| HUONG_DAN_DAY_DU.md | Giải thích đầy đủ | ⭐⭐⭐ Rất chi tiết | Người viết tài liệu, developers |
| DOCUMENTATION.md | Tài liệu kỹ thuật | ⭐⭐⭐⭐ Chuyên sâu | Architects, developers |
| README.md | Overview (English) | ⭐⭐ Vừa phải | International users |
| FIX_MONGODB_CONNECTION.md | Troubleshooting | ⭐⭐ Chi tiết | Người gặp lỗi MongoDB |

---

## 🎓 LỘ TRÌNH HỌC TẬP

### Tuần 1: Hiểu cơ bản
- [ ] Đọc TOM_TAT.md
- [ ] Đọc QUICKSTART.md
- [ ] Chạy thử hệ thống theo hướng dẫn
- [ ] Xem dữ liệu trên MongoDB Compass

### Tuần 2: Hiểu sâu
- [ ] Đọc HUONG_DAN_DAY_DU.md
- [ ] Đọc DOCUMENTATION.md
- [ ] Đọc code trong databridge.py
- [ ] Đọc code trong pc_monitor.py
- [ ] Thử modify code (thêm sensors mới)

### Tuần 3: Customize
- [ ] Thêm PC thứ 2 để monitor
- [ ] Thêm dashboard visualization
- [ ] Thêm email alerts khi offline
- [ ] Export data sang Excel/CSV

---

## 🔍 TÌM KIẾM NHANH

### Tôi cần tìm...

**"Cách kết nối MongoDB Atlas"**
→ HUONG_DAN_DAY_DU.md → PHẦN 2

**"Giải thích Data Bridge"**
→ HUONG_DAN_DAY_DU.md → PHẦN 1, Mục 1.2

**"Cấu trúc dữ liệu trong MongoDB"**
→ HUONG_DAN_DAY_DU.md → PHẦN 1, Mục 1.4
→ DOCUMENTATION.md → PHẦN 4

**"Cách detect PC offline"**
→ HUONG_DAN_DAY_DU.md → Mục "LAST WILL TESTAMENT"

**"AAS Model structure"**
→ DOCUMENTATION.md → PHẦN 6

**"MQTT Topics structure"**
→ TOM_TAT.md → Mục "LUỒNG DỮ LIỆU"
→ HUONG_DAN_DAY_DU.md → PHẦN 2

**"Thresholds và alerts"**
→ HUONG_DAN_DAY_DU.md → databridge.py → Mục "Kiểm tra Thresholds"

**"Encode password MongoDB"**
→ FIX_MONGODB_CONNECTION.md

---

## 💡 TIPS

### Khi đọc tài liệu:
1. Bắt đầu từ TOM_TAT.md để có overview
2. Không đọc hết một lúc - chia nhỏ
3. Đọc kèm với chạy code để hiểu rõ hơn
4. Note lại những phần quan trọng

### Khi viết báo cáo/tài liệu:
1. Copy kiến trúc diagram từ DOCUMENTATION.md
2. Copy code examples từ HUONG_DAN_DAY_DU.md
3. Copy MongoDB queries từ các file tài liệu
4. Thêm screenshots từ hệ thống thực tế

### Khi gặp lỗi:
1. Kiểm tra FIX_MONGODB_CONNECTION.md trước
2. Chạy check_system.py để diagnose
3. Xem logs: `docker-compose logs -f`
4. Search trong tài liệu theo keyword

---

## 📞 SUPPORT

### Câu hỏi thường gặp

**Q: File nào quan trọng nhất?**  
A: HUONG_DAN_DAY_DU.md - Có đầy đủ thông tin để viết tài liệu

**Q: Tôi không có MongoDB Atlas connection string thật?**  
A: Xem FIX_MONGODB_CONNECTION.md để lấy connection string từ MongoDB Atlas UI

**Q: Tôi muốn thêm sensor mới (ví dụ: GPU)?**  
A: Đọc HUONG_DAN_DAY_DU.md → Mục "PC Monitor" → Thêm function `get_gpu_info()`

**Q: Tôi muốn alert qua email?**  
A: Đọc databridge.py → Function `create_event()` → Thêm email sending code

---

## 🎉 KẾT LUẬN

Bạn có **6 files tài liệu đầy đủ** để:
- ✅ Hiểu hệ thống
- ✅ Chạy thử
- ✅ Viết báo cáo/tài liệu
- ✅ Customize và mở rộng

**Bắt đầu từ TOM_TAT.md và làm theo lộ trình!**

---

**Chúc bạn thành công! 📖**
