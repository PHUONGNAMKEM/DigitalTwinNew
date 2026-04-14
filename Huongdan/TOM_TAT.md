# 📋 TÓM TẮT HỆ THỐNG DIGITAL TWIN

## 🎯 MỤC TIÊU
Giám sát máy tính (PC) realtime, theo dõi trạng thái ON/OFF, tạo Digital Twin theo chuẩn Industry 4.0

---

## 🏗️ KIẾN TRÚC ĐƠN GIẢN

```
PC (máy thật) → MQTT → Data Bridge → MongoDB Atlas (Cloud)
                           ↓
                     AAS Framework (Digital Twin)
```

---

## 📁 CÁC FILE CHÍNH

### 1. docker-compose.yml
- **Thay đổi:** Thêm kết nối MongoDB Atlas
- **Thêm:** 3 biến môi trường cho mỗi service (aas-registry, aas-server)
  ```yaml
  - BASYX_BACKEND=MongoDB
  - BASYX_MONGODB_DBNAME=DigitalTwinDB
  - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://...
  ```

### 2. databridge.py - CẦU NỐI
- **Nhiệm vụ:** Nhận dữ liệu MQTT → Lưu MongoDB → Tạo AAS Model
- **Subscribe 3 topics:**
  - `industry/pc/+/telemetry` - Dữ liệu CPU, RAM, Disk
  - `industry/pc/+/status` - Online/Offline
  - `industry/pc/+/heartbeat` - Xác nhận còn sống

### 3. pc_monitor.py - THU THẬP DỮ LIỆU
- **Nhiệm vụ:** Đọc thông tin PC thật → Gửi qua MQTT
- **Thu thập:** CPU, RAM, Disk, Network, Uptime
- **Tần suất:** 5 giây/lần
- **Last Will:** Tự động gửi "offline" khi mất kết nối

---

## 🗄️ MONGODB COLLECTIONS

| Collection | Chức năng |
|-----------|-----------|
| `telemetry_history` | Lưu lịch sử tất cả dữ liệu (CPU, RAM, Disk...) |
| `pc_status` | Trạng thái hiện tại của từng PC (online/offline) |
| `aas_models` | Asset Administration Shell models |
| `events` | Cảnh báo và sự kiện (status change, threshold exceeded) |

---

## 🔄 LUỒNG DỮ LIỆU

### 1. Luồng Telemetry
```
pc_monitor.py thu thập (CPU: 45%, RAM: 60%)
    ↓ Publish MQTT
    ↓ Topic: industry/pc/PC001/telemetry
MQTT Broker
    ↓ Subscribe
databridge.py
    ↓ Lưu vào MongoDB: telemetry_history
    ↓ Kiểm tra thresholds (nếu > 90% → alert)
    ↓ Cập nhật AAS Model
```

### 2. Luồng Status (Online/Offline)
```
pc_monitor.py khởi động
    ↓ Publish "online"
    ↓ Topic: industry/pc/PC001/status
    ↓ + Setup Last Will (nếu mất kết nối → "offline")
MQTT Broker
    ↓
databridge.py
    ↓ So sánh status cũ vs mới
    ↓ Nếu thay đổi → Tạo Event
    ↓ Lưu vào MongoDB: pc_status & events
```

---

## 🚀 CÁCH CHẠY (3 BƯỚC)

### Bước 1: Docker Containers
```powershell
docker-compose up -d
```

### Bước 2: Data Bridge (Terminal 1)
```powershell
python databridge.py
```

### Bước 3: PC Monitor (Terminal 2)
```powershell
python pc_monitor.py
```

**Output:**
```
📊 [10:30:00] Telemetry:
   CPU: 45.2% | RAM: 60.1% | Disk: 70.5%
💓 [10:30:30] Heartbeat sent
```

---

## 📊 XEM DỮ LIỆU

### MongoDB Compass
1. Kết nối: `mongodb+srv://sa:Admin@123@cluster0.wrpp0cf.mongodb.net`
2. Database: `DigitalTwinDB`
3. Xem collections: telemetry_history, pc_status, events

### AAS GUI
- URL: http://localhost:3000
- Xem Digital Twin models

---

## ⚙️ CẤU HÌNH QUAN TRỌNG

### Connection String MongoDB
```
mongodb+srv://sa:Admin@123@cluster0.wrpp0cf.mongodb.net/DigitalTwinDB
```

**Sử dụng trong:**
- `docker-compose.yml` (2 nơi: aas-registry, aas-server)
- `databridge.py`

### Device Configuration (pc_monitor.py)
```python
DEVICE_ID = "PC001"       # ID duy nhất
DEVICE_NAME = "Workstation-01"
LOCATION = "Workshop Floor 1"
```

### Alert Thresholds (databridge.py)
```python
ALERT_THRESHOLDS = {
    "cpu_usage": 90.0,           # CPU > 90%
    "ram_usage_percent": 85.0,   # RAM > 85%
    "disk_usage_percent": 90.0   # Disk > 90%
}
```

---

## 🔍 KIỂM TRA STATUS

### Xem PC đang online
```javascript
// MongoDB Query
db.pc_status.find({ status: "online" })
```

### Xem events chưa xử lý
```javascript
db.events.find({ acknowledged: false }).sort({ timestamp: -1 })
```

### Xem CPU usage trung bình 24h
```javascript
db.telemetry_history.aggregate([
  { $match: {
      device_id: "PC001",
      timestamp: { $gte: new Date(Date.now() - 24*60*60*1000) }
  }},
  { $group: {
      _id: "$device_id",
      avg_cpu: { $avg: "$cpu_usage" },
      max_cpu: { $max: "$cpu_usage" }
  }}
])
```

---

## 🎓 GIẢI THÍCH CHO TÀI LIỆU

### 1. TẠI SAO PHẢI DÙNG MONGODB ATLAS?
- **Lưu trữ lâu dài:** Dữ liệu không mất khi restart
- **Cloud-based:** Truy cập từ mọi nơi
- **Scalable:** Tự động mở rộng
- **Backup:** Tự động backup hàng ngày

### 2. DATA BRIDGE LÀM GÌ?
- **Thu thập:** Nhận dữ liệu từ MQTT
- **Lưu trữ:** Ghi vào MongoDB Atlas
- **Phân tích:** Kiểm tra thresholds
- **Cảnh báo:** Tạo events khi có vấn đề
- **Digital Twin:** Cập nhật AAS models

### 3. LAST WILL TESTAMENT LÀ GÌ?
- Cơ chế của MQTT để phát hiện disconnect
- Khi PC mất kết nối → MQTT Broker tự động gửi "offline"
- Data Bridge nhận được và cập nhật status

### 4. AAS MODEL LÀ GÌ?
- Asset Administration Shell - Chuẩn Industry 4.0
- Mô hình số của thiết bị vật lý
- Chứa:
  - **Identification:** Thông tin nhận dạng
  - **Submodels:** Các mô hình con
    - TechnicalData: CPU, RAM, Disk
    - OperationalData: Status, Uptime

---

## 🎯 DEMO SCENARIOS

### Scenario 1: PC đang chạy bình thường
- Monitor gửi telemetry mỗi 5s
- Data Bridge lưu vào MongoDB
- AAS model được cập nhật

### Scenario 2: PC bị tắt đột ngột
- MQTT phát hiện mất kết nối
- Gửi Last Will: "offline"
- Data Bridge tạo event "status_change"
- MongoDB cập nhật: pc_status.status = "offline"

### Scenario 3: CPU quá tải
- Monitor đọc CPU = 95%
- Data Bridge so sánh với threshold (90%)
- Vượt ngưỡng → Tạo event "threshold_exceeded"
- Console hiển thị: "⚠️ ALERT: CPU usage cao"

---

## 📞 SUPPORT

### Logs kiểm tra
```powershell
# Docker containers
docker-compose logs -f

# PC Monitor
python pc_monitor.py

# Data Bridge  
python databridge.py
```

### Common Issues
1. **MongoDB connection failed** → Kiểm tra Network Access
2. **MQTT refused** → Kiểm tra docker ps | findstr mqtt
3. **No data** → Kiểm tra topics match nhau

---

**📖 Xem thêm tài liệu chi tiết:**
- `DOCUMENTATION.md` - Kiến trúc và luồng dữ liệu chi tiết
- `HUONG_DAN_DAY_DU.md` - Hướng dẫn đầy đủ từng bước
- `QUICKSTART.md` - Hướng dẫn nhanh (Tiếng Việt)
- `README.md` - Tổng quan hệ thống (English)

**🎉 HOÀN THÀNH! Chúc viết tài liệu thuận lợi!**
