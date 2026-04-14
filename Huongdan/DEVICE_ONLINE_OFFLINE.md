# Hướng dẫn: Giả lập thiết bị Online/Offline

## ❓ Câu hỏi: Làm sao biết thiết bị đang Online hay Offline?

### Cơ chế hoạt động:

```
┌─────────────────────────────────────────────────────────┐
│  THIẾT BỊ                                               │
├─────────────────────────────────────────────────────────┤
│  Operational Data:                                      │
│  ├─ CPUUsage: 45.2%                                     │
│  ├─ MemoryUsage: 60.5%                                  │
│  └─ Timestamp: 2026-02-04T15:30:00Z  ← QUAN TRỌNG!    │
└─────────────────────────────────────────────────────────┘
                       ↓
            ┌──────────────────────┐
            │   CHECK TIMESTAMP    │
            └──────────────────────┘
                       ↓
        ╔══════════════════════════════╗
        ║  Now - Timestamp < 60s?      ║
        ╚══════════════════════════════╝
                ↙              ↘
            YES                   NO
             ↓                     ↓
        🟢 ONLINE            🔴 OFFLINE
```

**Quy tắc:**
- **ONLINE** = Timestamp được cập nhật trong vòng 60 giây gần nhất
- **OFFLINE** = Timestamp quá 60 giây HOẶC không có

## 🎯 Các cách để thiết bị hiển thị Online:

### **Cách 1: Tự động cập nhật tất cả thiết bị** ⭐ Khuyên dùng

Chạy script tự động giả lập:

```powershell
python generic_device_updater.py
```

Script sẽ:
- ✅ Tự động phát hiện TẤT CẢ thiết bị trong hệ thống
- ✅ Tự động nhận biết loại thiết bị (Computer, Medical, IoT...)
- ✅ Giả lập dữ liệu phù hợp cho từng loại
- ✅ Cập nhật mỗi 10 giây
- ✅ Thiết bị sẽ hiển thị **ONLINE** 🟢

**Output mẫu:**
```
============================================================
🤖 GENERIC DEVICE UPDATER
============================================================
API URL: http://localhost:5000/api
Update Interval: 10 seconds
============================================================
✓ Connected to Device Manager API

Starting monitoring loop...
Press Ctrl+C to stop

[15:30:00] Updating 3 device(s):
----------------------------------------------------------------------
[PC-001] ✓ Updated 7/7 fields - Dell Precision 5820
[MED-001] ✓ Updated 6/6 fields - MRI Scanner
[3DP-001] ✓ Updated 8/8 fields - Ultimaker S5
----------------------------------------------------------------------

[15:30:10] Updating 3 device(s):
...
```

### **Cách 2: Cập nhật một thiết bị cụ thể**

Chỉ cập nhật 1 lần cho 1 thiết bị:

```powershell
python generic_device_updater.py --device PC-001
```

→ Thiết bị sẽ online trong 60 giây, sau đó offline

### **Cách 3: Tùy chỉnh interval**

Cập nhật nhanh hơn (mỗi 5 giây):

```powershell
python generic_device_updater.py --interval 5
```

### **Cách 4: Dùng API trực tiếp**

Gọi API để cập nhật:

```python
import requests
from datetime import datetime

device_id = "PC-001"

data = {
    "CPUUsage": 45.2,
    "MemoryUsage": 60.5,
    "DiskUsage": 70.0,
    "Timestamp": datetime.utcnow().isoformat() + "Z"
}

response = requests.put(
    f"http://localhost:5000/api/devices/{device_id}/operational",
    json=data
)

print(response.json())
```

### **Cách 5: Sử dụng pc_monitor cho máy thật**

Nếu muốn theo dõi máy tính thật:

```powershell
python pc_monitor_integrated.py
```

→ Cập nhật dữ liệu CPU, RAM, Disk thật từ máy tính

## 📊 Dữ liệu được giả lập

Script `generic_device_updater.py` tự động nhận biết và giả lập:

### Computer/Workstation 💻
```json
{
  "CPUUsage": 45.2,
  "MemoryUsage": 60.5,
  "DiskUsage": 70.0,
  "NetworkSent": 1500.5,
  "NetworkReceived": 3200.8,
  "Timestamp": "2026-02-04T15:30:00Z"
}
```

### Medical Device 🏥
```json
{
  "OperationalStatus": "Running",
  "TotalScans": 1523,
  "ErrorCode": "NONE",
  "Timestamp": "2026-02-04T15:30:00Z"
}
```

### 3D Printer 🖨️
```json
{
  "PrintStatus": "Printing",
  "PrintProgress": 45.5,
  "NozzleTemperature": 205.0,
  "BedTemperature": 60.0,
  "MaterialRemaining": 850.0,
  "Timestamp": "2026-02-04T15:30:00Z"
}
```

### IoT Sensor 📡
```json
{
  "SensorValue": 25.5,
  "BatteryLevel": 85.0,
  "SignalStrength": -65.0,
  "ErrorCount": 0,
  "Timestamp": "2026-02-04T15:30:00Z"
}
```

### Construction Equipment 🏗️
```json
{
  "EngineStatus": "Running",
  "FuelLevel": 75.5,
  "EngineHours": 1245.5,
  "EngineTemperature": 85.0,
  "GPSLocation": "10.123456,106.789012",
  "Timestamp": "2026-02-04T15:30:00Z"
}
```

## 🚀 Quy trình làm việc đầy đủ

### Bước 1: Khởi động hệ thống

```powershell
# Terminal 1: Docker containers
docker-compose up -d

# Terminal 2: Flask web app
python device_manager_web.py

# Terminal 3: Device updater
python generic_device_updater.py
```

### Bước 2: Tạo thiết bị mới

1. Mở: http://localhost:5000
2. Click "Thêm thiết bị mới"
3. Chọn template và điền thông tin
4. Submit

→ Thiết bị được tạo nhưng hiển thị **OFFLINE** 🔴

### Bước 3: Tự động Online

Script `generic_device_updater.py` đang chạy sẽ:
- Phát hiện thiết bị mới
- Bắt đầu cập nhật dữ liệu
- Sau 1 lần cập nhật → Thiết bị chuyển **ONLINE** 🟢

### Bước 4: Xem kết quả

- Dashboard tự động refresh mỗi 5 giây
- Status badge chuyển từ 🔴 offline → 🟢 online
- Thống kê cập nhật: Online devices tăng

## 🔧 Troubleshooting

### ❓ Thiết bị vẫn offline sau khi chạy updater?

**Kiểm tra:**
1. Script có đang chạy không?
2. Có lỗi trong console không?
3. Device ID có đúng không?

**Giải pháp:**
```powershell
# Test update 1 lần
python generic_device_updater.py --device YOUR-DEVICE-ID

# Xem log
```

### ❓ Làm sao xem dữ liệu được cập nhật?

**Cách 1: Qua API**
```powershell
curl http://localhost:5000/api/devices/PC-001
```

**Cách 2: BaSyx Web UI**
1. Mở: http://localhost:3000
2. Chọn AAS của thiết bị
3. Mở Submodel "OperationalData"
4. Xem giá trị các properties

**Cách 3: Dashboard**
- Xem "Cập nhật lần cuối" trên card thiết bị

### ❓ Muốn thay đổi thời gian timeout?

Sửa trong `device_manager_web.py`:

```python
DEVICE_TIMEOUT = 60  # Đổi thành 120 (2 phút), 300 (5 phút)...
```

## 💡 Tips & Tricks

### 1. Chạy nhiều updater với interval khác nhau

```powershell
# Fast update (5s)
python generic_device_updater.py --interval 5

# Slow update (30s)
python generic_device_updater.py --interval 30
```

### 2. Cập nhật chỉ thiết bị quan trọng

Sửa `generic_device_updater.py`, thêm filter:

```python
devices = get_all_devices()
# Chỉ update devices có ID bắt đầu bằng "PROD-"
devices = [d for d in devices if d['id'].startswith('PROD-')]
```

### 3. Giả lập thiết bị lỗi

Update với error code:

```python
data = {
    "OperationalStatus": "Error",
    "ErrorCode": "E001",
    "Timestamp": datetime.utcnow().isoformat() + "Z"
}
```

### 4. Tạo pattern cập nhật đặc biệt

VD: Thiết bị chỉ online trong giờ làm việc:

```python
from datetime import datetime

now = datetime.now()
if 8 <= now.hour < 18:  # 8AM - 6PM
    update_device(device_id)
```

## 📝 Tóm tắt

| Tình huống | Giải pháp | Lệnh |
|------------|-----------|------|
| Tất cả thiết bị online | Generic updater | `python generic_device_updater.py` |
| 1 thiết bị online | Single update | `python generic_device_updater.py --device ID` |
| Máy tính thật | PC Monitor | `python pc_monitor_integrated.py` |
| Update nhanh | Custom interval | `python generic_device_updater.py --interval 5` |
| Giả lập nhiều thiết bị | Device simulator | `python device_simulator.py` |

**Quan trọng:** Timestamp phải được cập nhật liên tục để thiết bị hiển thị online! 🕒
