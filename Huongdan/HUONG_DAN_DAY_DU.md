# 📖 HƯỚNG DẪN SỬ DỤNG CHI TIẾT - DIGITAL TWIN PC MONITORING

## 🎯 MỤC ĐÍCH

Hệ thống giám sát trạng thái máy tính (PC) realtime và tạo Digital Twin trong môi trường công nghiệp.

**Các chức năng chính:**
1. ✅ Giám sát CPU, RAM, Disk, Network realtime
2. ✅ Theo dõi trạng thái Online/Offline
3. ✅ Lưu trữ dữ liệu vào MongoDB Atlas (Cloud)
4. ✅ Tạo Asset Administration Shell (AAS) Models theo chuẩn Industry 4.0
5. ✅ Cảnh báo khi vượt ngưỡng
6. ✅ Dashboard để theo dõi

---

# PHẦN 1: GIẢI THÍCH CÁC FILE

## 1.1 docker-compose.yml

**Mục đích:** Cấu hình các Docker containers cho hệ thống BaSyx

**Các thay đổi quan trọng:**

### ❓ TẠI SAO PHẢI THAY ĐỔI?

Ban đầu, AAS Registry và AAS Server lưu dữ liệu trong RAM (InMemory). Khi restart container, tất cả dữ liệu bị mất!

**Giải pháp:** Kết nối tới MongoDB Atlas (Cloud Database) để lưu trữ lâu dài.

### 📝 THAY ĐỔI CỤ THỂ:

```yaml
# TRƯỚC:
aas-registry:
  environment:
    - BASYX_REGISTRY_PATH=registry

# SAU:
aas-registry:
  environment:
    - BASYX_REGISTRY_PATH=registry
    - BASYX_BACKEND=MongoDB  # ← Sử dụng MongoDB thay vì InMemory
    - BASYX_MONGODB_DBNAME=DigitalTwinDB  # ← Tên database
    - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://...  # ← Connection string
```

**Giải thích từng biến:**
- `BASYX_BACKEND=MongoDB`: Chuyển backend từ InMemory sang MongoDB
- `BASYX_MONGODB_DBNAME`: Tên database trên MongoDB Atlas
- `BASYX_MONGODB_CONNECTIONURL`: Chuỗi kết nối đầy đủ

**Định dạng Connection String:**
```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>
```

**Ví dụ của bạn:**
```
mongodb+srv://sa:Admin@123@cluster0.wrpp0cf.mongodb.net/DigitalTwinDB
```

---

## 1.2 databridge.py - CẦU NỐI DỮ LIỆU

**Mục đích:** Kết nối MQTT Broker với MongoDB Atlas và BaSyx AAS Framework

### 🌉 DATABRIDGE LÀ GÌ?

Data Bridge là "cầu nối" trung tâm của hệ thống:

```
PC Monitor (Thu thập dữ liệu)
     ↓ Publish MQTT
MQTT Broker (Message Queue)
     ↓ Subscribe
DATA BRIDGE ← ĐÂY LÀ CẦU NỐI
     ↓ ↓ ↓
     ↓ ↓ └─→ BaSyx AAS (Tạo Digital Twin Model)
     ↓ └───→ Create Events (Cảnh báo)
     └─────→ MongoDB Atlas (Lưu dữ liệu)
```

### 📦 CÁC CHỨC NĂNG:

#### **1. Subscribe MQTT Topics**

```python
MQTT_TOPICS = [
    "industry/pc/+/telemetry",  # Dữ liệu kỹ thuật (CPU, RAM, Disk)
    "industry/pc/+/status",     # Trạng thái (online/offline)
    "industry/pc/+/heartbeat"   # Xác nhận còn sống
]
```

**Giải thích:**
- `+` là wildcard, match bất kỳ device_id nào
- Ví dụ: `industry/pc/PC001/telemetry`, `industry/pc/PC002/telemetry`

#### **2. Xử lý Telemetry Data**

```python
def handle_telemetry(self, topic, data):
    # Lưu vào MongoDB collection: telemetry_history
    self.telemetry_collection.insert_one(data)
    
    # Kiểm tra ngưỡng cảnh báo
    self.check_thresholds(device_id, data)
    
    # Cập nhật AAS Model
    self.update_aas_model(device_id, data)
```

**Dữ liệu được lưu:**
```json
{
  "device_id": "PC001",
  "timestamp": "2026-01-01T10:30:00",
  "cpu_usage": 45.2,
  "ram_usage_percent": 60.1,
  "disk_usage_percent": 70.5,
  "cpu_temperature": 55.0,
  "uptime_seconds": 86400
}
```

#### **3. Xử lý Status Changes (Online/Offline)**

```python
def handle_status(self, topic, data):
    # Cập nhật status trong MongoDB
    self.status_collection.update_one(
        {"device_id": device_id},
        {"$set": {"status": status, "last_seen": timestamp}},
        upsert=True
    )
    
    # Nếu status thay đổi → Tạo Event
    if old_status != new_status:
        self.create_event(
            event_type="status_change",
            event_data={"old": old_status, "new": new_status},
            severity="warning"
        )
```

**Event được tạo:**
```json
{
  "device_id": "PC001",
  "event_type": "status_change",
  "event_data": {
    "old_status": "online",
    "new_status": "offline"
  },
  "severity": "warning",
  "timestamp": "2026-01-01T10:30:00",
  "acknowledged": false
}
```

#### **4. Kiểm tra Thresholds (Ngưỡng cảnh báo)**

```python
ALERT_THRESHOLDS = {
    "cpu_usage": 90.0,           # CPU > 90%
    "ram_usage_percent": 85.0,   # RAM > 85%
    "disk_usage_percent": 90.0   # Disk > 90%
}

def check_thresholds(self, device_id, data):
    if data['cpu_usage'] > 90:
        self.create_event(
            event_type="threshold_exceeded",
            event_data={"alert": "CPU usage cao"},
            severity="warning"
        )
```

#### **5. Tạo/Cập nhật AAS Model**

```python
def update_aas_model(self, device_id, telemetry_data):
    aas_model = {
        "aas_id": f"{device_id}_AAS",
        "device_id": device_id,
        "identification": {...},
        "submodels": [
            {
                "idShort": "TechnicalData",
                "properties": {
                    "cpu_usage": telemetry_data['cpu_usage'],
                    "ram_usage_percent": telemetry_data['ram_usage_percent']
                }
            },
            {
                "idShort": "OperationalData",
                "properties": {
                    "status": "online",
                    "uptime_seconds": telemetry_data['uptime_seconds']
                }
            }
        ]
    }
    
    # Lưu vào MongoDB collection: aas_models
    self.aas_collection.update_one(
        {"device_id": device_id},
        {"$set": aas_model},
        upsert=True
    )
```

---

## 1.3 pc_monitor.py - GIÁM SÁT MÁY TÍNH

**Mục đích:** Thu thập thông tin máy tính thực tế và gửi qua MQTT

### 🖥️ PC MONITOR LÀM GÌ?

```
1. Đọc thông tin hệ thống (mỗi 5 giây)
   ├─ CPU: Usage %, Frequency, Temperature
   ├─ RAM: Total, Used, Available, %
   ├─ Disk: Total, Used, Free, %
   ├─ Network: Bytes sent/recv
   └─ System: Uptime, Boot time
   
2. Format thành JSON

3. Publish lên MQTT
   Topic: industry/pc/PC001/telemetry
   
4. Gửi Status khi khởi động
   Topic: industry/pc/PC001/status
   Payload: {"status": "online"}
   
5. Setup Last Will
   Nếu mất kết nối → MQTT tự động gửi "offline"
```

### 📊 DỮ LIỆU THU THẬP:

#### **CPU Information**
```python
def get_cpu_info():
    return {
        "cpu_usage": 45.2,           # % sử dụng
        "cpu_count": 8,               # Số cores
        "cpu_frequency_current": 3200.0,  # MHz hiện tại
        "cpu_frequency_max": 4500.0,      # MHz tối đa
        "cpu_temperature": 55.0       # °C (nếu có sensor)
    }
```

#### **Memory (RAM) Information**
```python
def get_memory_info():
    return {
        "ram_total_mb": 16384,        # Tổng RAM (MB)
        "ram_used_mb": 9830,          # RAM đang dùng (MB)
        "ram_available_mb": 6554,     # RAM còn trống (MB)
        "ram_usage_percent": 60.1,    # % sử dụng
        "swap_total_mb": 8192,        # Swap memory total
        "swap_used_mb": 1024,         # Swap memory used
        "swap_usage_percent": 12.5    # Swap % used
    }
```

#### **Disk Information**
```python
def get_disk_info():
    return {
        "disk_total_gb": 500.0,       # Tổng dung lượng (GB)
        "disk_used_gb": 350.0,        # Đã sử dụng (GB)
        "disk_free_gb": 150.0,        # Còn trống (GB)
        "disk_usage_percent": 70.0,   # % sử dụng
        "disk_read_mb": 1234.5,       # Tổng MB đọc
        "disk_write_mb": 5678.9       # Tổng MB ghi
    }
```

#### **Network Information**
```python
def get_network_info():
    return {
        "network_bytes_sent": 123456789,   # Bytes gửi đi
        "network_bytes_recv": 987654321,   # Bytes nhận về
        "network_packets_sent": 12345,     # Packets gửi
        "network_packets_recv": 98765,     # Packets nhận
        "network_errors_in": 0,            # Lỗi nhận
        "network_errors_out": 0            # Lỗi gửi
    }
```

#### **System Uptime**
```python
def get_boot_time():
    return {
        "boot_time": "2026-01-01T08:00:00",  # Thời gian boot
        "uptime_seconds": 86400,              # Thời gian chạy (giây)
        "uptime_hours": 24.0                  # Thời gian chạy (giờ)
    }
```

### 🔄 LAST WILL TESTAMENT

**Vấn đề:** Nếu máy tính tắt đột ngột hoặc mất mạng, làm sao biết nó offline?

**Giải pháp:** MQTT Last Will Testament

```python
# Setup Last Will khi kết nối MQTT
mqtt_client.will_set(
    topic="industry/pc/PC001/status",
    payload=json.dumps({"status": "offline", "reason": "connection_lost"}),
    qos=1,
    retain=True  # Lưu message cuối cùng
)
```

**Cách hoạt động:**
1. PC Monitor kết nối MQTT và set Last Will
2. Nếu kết nối bị mất (PC tắt, mất mạng, crash)
3. MQTT Broker tự động publish message "offline" 
4. Data Bridge nhận được và cập nhật status

---

## 1.4 CÁC COLLECTIONS TRONG MONGODB

### **Collection: telemetry_history**

**Mục đích:** Lưu lịch sử tất cả dữ liệu telemetry

```json
{
  "_id": ObjectId("..."),
  "device_id": "PC001",
  "timestamp": ISODate("2026-01-01T10:30:00Z"),
  "cpu_usage": 45.2,
  "cpu_temperature": 55.0,
  "ram_usage_percent": 60.1,
  "ram_total_mb": 16384,
  "disk_usage_percent": 70.5,
  "network_bytes_sent": 123456789,
  "uptime_seconds": 86400
}
```

**Queries thường dùng:**
```javascript
// Lấy dữ liệu 24h gần nhất của PC001
db.telemetry_history.find({
  device_id: "PC001",
  timestamp: { $gte: new Date(Date.now() - 24*60*60*1000) }
}).sort({ timestamp: -1 })

// Tính CPU usage trung bình
db.telemetry_history.aggregate([
  { $match: { device_id: "PC001" } },
  { $group: { 
      _id: "$device_id",
      avg_cpu: { $avg: "$cpu_usage" }
  }}
])
```

### **Collection: pc_status**

**Mục đích:** Lưu trạng thái hiện tại của từng PC

```json
{
  "_id": ObjectId("..."),
  "device_id": "PC001",
  "status": "online",
  "last_seen": ISODate("2026-01-01T10:30:00Z"),
  "device_info": {
    "device_name": "Workstation-01",
    "hostname": "WS-01",
    "ip_address": "192.168.1.100",
    "os": "Windows 11",
    "location": "Workshop Floor 1"
  }
}
```

**Queries thường dùng:**
```javascript
// Lấy tất cả PC đang online
db.pc_status.find({ status: "online" })

// Lấy PC offline lâu hơn 5 phút
db.pc_status.find({
  status: "online",
  last_seen: { $lt: new Date(Date.now() - 5*60*1000) }
})
```

### **Collection: aas_models**

**Mục đích:** Lưu Asset Administration Shell models

```json
{
  "_id": ObjectId("..."),
  "aas_id": "PC001_AAS",
  "device_id": "PC001",
  "identification": {
    "id": "https://digitaltwin.example.com/aas/PC001",
    "idType": "IRI"
  },
  "submodels": [
    {
      "idShort": "TechnicalData",
      "properties": {
        "cpu_usage": 45.2,
        "ram_usage_percent": 60.1
      }
    },
    {
      "idShort": "OperationalData",
      "properties": {
        "status": "online",
        "uptime_seconds": 86400
      }
    }
  ],
  "last_update": ISODate("2026-01-01T10:30:00Z")
}
```

### **Collection: events**

**Mục đích:** Lưu các sự kiện quan trọng

```json
{
  "_id": ObjectId("..."),
  "device_id": "PC001",
  "event_type": "status_change",  // hoặc "threshold_exceeded"
  "event_data": {
    "old_status": "online",
    "new_status": "offline"
  },
  "severity": "warning",  // info, warning, critical
  "timestamp": ISODate("2026-01-01T10:30:00Z"),
  "acknowledged": false
}
```

**Queries thường dùng:**
```javascript
// Lấy events chưa acknowledged
db.events.find({ acknowledged: false }).sort({ timestamp: -1 })

// Lấy events của PC001 trong 1h qua
db.events.find({
  device_id: "PC001",
  timestamp: { $gte: new Date(Date.now() - 60*60*1000) }
})
```

---

# PHẦN 2: HƯỚNG DẪN SỬ DỤNG

## Bước 1: Khởi động Docker Containers

```powershell
cd C:\Users\PHONG\Downloads\DigitalTwin
docker-compose up -d
```

**Kiểm tra:**
```powershell
docker-compose ps
```

Output mong muốn:
```
NAME          STATUS
mqtt-broker   Up
aas-registry  Up
aas-server    Up
aas-gui       Up
```

## Bước 2: Khởi động Data Bridge

**Terminal 1:**
```powershell
python databridge.py
```

Output mong muốn:
```
===========================================================
🌉 BaSyx Data Bridge đang khởi động...
============================================================
⏳ Đang kết nối MongoDB Atlas...
✓ Đã kết nối MongoDB Atlas
  Database: DigitalTwinDB
  Collections: telemetry_history, pc_status, aas_models, events

✓ Đã kết nối MQTT Broker: localhost:1883
✓ Đã subscribe: industry/pc/+/telemetry
✓ Đã subscribe: industry/pc/+/status
✓ Đã subscribe: industry/pc/+/heartbeat

✓ Data Bridge đã sẵn sàng!
⏳ Đang chờ dữ liệu từ MQTT...
```

## Bước 3: Khởi động PC Monitor

**Terminal 2:**
```powershell
python pc_monitor.py
```

Output mong muốn:
```
============================================================
🖥️  PC MONITOR - PC001
============================================================
Device: Workstation-01
Location: Workshop Floor 1
MQTT Broker: localhost:1883
============================================================

⏳ Đang kết nối MQTT Broker...
✓ Đã kết nối MQTT Broker: localhost:1883
✓ Đã gửi status: ONLINE

✅ Bắt đầu giám sát... (Nhấn Ctrl+C để dừng)

📊 [10:30:00] Telemetry:
   CPU: 45.2% | RAM: 60.1% | Disk: 70.5%
💓 [10:30:30] Heartbeat sent
```

## Bước 4: Xem dữ liệu trên MongoDB Atlas

1. Mở **MongoDB Compass** hoặc **MongoDB Atlas Web UI**
2. Kết nối tới: `mongodb+srv://sa:Admin@123@cluster0.wrpp0cf.mongodb.net`
3. Chọn database: `DigitalTwinDB`
4. Xem các collections:
   - `telemetry_history` - Dữ liệu realtime
   - `pc_status` - Trạng thái PC
   - `aas_models` - Digital Twin models
   - `events` - Cảnh báo/sự kiện

## Bước 5: Xem AAS GUI

Mở trình duyệt: http://localhost:3000

---

# PHẦN 3: DEMO SCENARIOS

## Scenario 1: Giám sát PC realtime

**Khi chạy:**
1. PC Monitor thu thập dữ liệu mỗi 5 giây
2. Data Bridge nhận và lưu vào MongoDB
3. Xem dữ liệu realtime trên MongoDB Compass

## Scenario 2: Phát hiện PC offline

**Test:**
1. Đang chạy PC Monitor
2. Nhấn Ctrl+C để stop
3. → Data Bridge nhận "offline" status
4. → Event được tạo trong collection `events`
5. → Status trong `pc_status` được cập nhật

## Scenario 3: Cảnh báo CPU cao

**Test:**
1. Chạy chương trình nặng để CPU lên > 90%
2. → Data Bridge phát hiện vượt threshold
3. → Event "threshold_exceeded" được tạo
4. → Console hiển thị: "⚠️ ALERT: PC001 - CPU usage cao: 95.2%"

---

# PHẦN 4: TROUBLESHOOTING

## Lỗi: Cannot connect to MongoDB

**Nguyên nhân:**
- Connection string sai
- Network Access chưa whitelist IP
- Username/Password sai

**Giải pháp:**
1. Kiểm tra connection string trong `databridge.py`
2. Vào MongoDB Atlas → Network Access → Add IP Address → Allow Access from Anywhere
3. Kiểm tra username/password

## Lỗi: MQTT Connection Refused

**Nguyên nhân:**
- MQTT Broker chưa chạy
- Port 1883 bị chặn

**Giải pháp:**
```powershell
# Kiểm tra MQTT Broker
docker ps | findstr mqtt

# Restart MQTT Broker
docker-compose restart mqtt-broker
```

## Lỗi: psutil not found

**Giải pháp:**
```powershell
pip install psutil
```

---

**🎉 HOÀN THÀNH! Bạn đã có hệ thống Digital Twin hoàn chỉnh!**
