# PC Monitor - BaSyx Integration Guide

## Tổng quan

**pc_monitor_integrated.py** là công cụ giám sát máy tính real-time tích hợp trực tiếp với BaSyx Digital Twin System.

### Tính năng chính:

✅ **Tự động khởi tạo Digital Twin**: Tạo AAS và Submodels nếu chưa tồn tại  
✅ **Cập nhật real-time**: Update dữ liệu vận hành mỗi 5 giây qua REST API  
✅ **Không cần MQTT/DataBridge**: Gọi trực tiếp API của BaSyx Server  
✅ **Persistent data**: Tất cả dữ liệu được lưu vào MongoDB tự động  

---

## Cấu trúc Digital Twin được tạo

### 1. Asset Administration Shell (AAS)
- **ID**: `https://example.com/ids/aas/PC001`
- **ID Short**: `PC001_AAS`
- **Asset Type**: Computer/Workstation

### 2. Submodels

#### 2.1 Nameplate (Thông tin cơ bản)
- ManufacturerName: Dell Technologies
- ManufacturerProductDesignation: Dell Precision 5820
- Hostname: Tên máy tính
- IPAddress: Địa chỉ IP
- Location: Vị trí vật lý

#### 2.2 TechnicalData (Thông số kỹ thuật)
- OperatingSystem: Windows/Linux version
- Processor: CPU model
- CPUCores: Số lõi CPU
- RAMSize: Tổng RAM (GB)
- DiskSize: Tổng dung lượng ổ đĩa (GB)
- Architecture: Kiến trúc hệ thống

#### 2.3 OperationalData (Dữ liệu vận hành - Real-time)
- **CPUUsage**: % sử dụng CPU (cập nhật mỗi 5s)
- **MemoryUsage**: RAM đã dùng (GB)
- **MemoryUsagePercent**: % RAM đã dùng
- **DiskUsage**: Disk đã dùng (GB)
- **DiskUsagePercent**: % Disk đã dùng
- **Status**: Trạng thái (Running/Stopped)
- **Uptime**: Thời gian hoạt động (giây)

---

## Cách sử dụng

### Bước 1: Khởi động BaSyx System

```bash
cd C:\Users\PHONG\Downloads\DigitalTwin
docker-compose up -d
```

Đợi khoảng 10 giây để các services khởi động đầy đủ.

### Bước 2: Chạy PC Monitor

```bash
python pc_monitor_integrated.py
```

### Output mẫu:

```
======================================================================
🖥️  PC MONITOR - BASYX INTEGRATED
======================================================================
Device ID: PC001
Device Name: Dell Precision 5820
Location: Workshop Floor 1
BaSyx Server: http://localhost:8081
======================================================================

⏳ Đang kiểm tra kết nối BaSyx Server...
✅ Kết nối BaSyx Server thành công!

======================================================================
🚀 KHỞI TẠO DIGITAL TWIN
======================================================================
📦 Đang tạo AAS cho PC001...
✅ Đã tạo AAS thành công!
📦 Đang tạo Nameplate Submodel...
✅ Đã tạo Nameplate Submodel thành công!
📦 Đang tạo Technical Data Submodel...
✅ Đã tạo Technical Data Submodel thành công!
📦 Đang tạo Operational Data Submodel...
✅ Đã tạo Operational Data Submodel thành công!
======================================================================
✅ Digital Twin đã sẵn sàng!
======================================================================

✅ Bắt đầu giám sát và cập nhật real-time (mỗi 5s)
   Nhấn Ctrl+C để dừng

📊 [22:15:04] Updated 6/7 properties:
   CPU: 23.1% | RAM: 66.9% (15.91GB) | Disk: 98.6% (270.84GB) | Uptime: 102h
📊 [22:15:09] Updated 6/7 properties:
   CPU: 19.8% | RAM: 66.7% (15.86GB) | Disk: 98.6% (270.84GB) | Uptime: 102h
```

### Bước 3: Xem dữ liệu trên AAS UI

1. Mở browser: **http://localhost:3000**
2. Click vào **PC001_AAS**
3. Click vào **OperationalData** submodel
4. Xem các giá trị đang được update real-time!

---

## So sánh với DataBridge

### Phương pháp 1: Sử dụng DataBridge (MQTT)

```
[PC Monitor] → MQTT → [DataBridge] → [BaSyx API] → [MongoDB]
```

**Ưu điểm:**
- Decoupling: Tách biệt data source và AAS
- Protocol flexibility: Hỗ trợ nhiều protocols
- Transformation: Transform dữ liệu linh hoạt

**Nhược điểm:**
- Phức tạp hơn: Cần config nhiều files
- Nhiều components: MQTT Broker + DataBridge
- Latency cao hơn: Qua nhiều layers

### Phương pháp 2: Direct API Integration (Script này)

```
[PC Monitor] → [BaSyx API] → [MongoDB]
```

**Ưu điểm:**
- ✅ Đơn giản: Chỉ 1 script Python
- ✅ Nhanh hơn: Gọi trực tiếp API
- ✅ Tự động khởi tạo: Tạo AAS nếu chưa có
- ✅ Dễ debug: Ít components hơn

**Nhược điểm:**
- Tight coupling: Script biết về cấu trúc AAS
- Single protocol: Chỉ dùng REST API

---

## Tùy chỉnh

### Thay đổi Device Information

Sửa các constants trong file:

```python
# Device Configuration - THAY ĐỔI THEO MÁY CỦA BẠN
DEVICE_ID = "PC002"  # Thay đổi ID
DEVICE_NAME = "HP Z8 G4"  # Thay đổi tên
LOCATION = "Lab Room 203"  # Thay đổi location
MANUFACTURER = "HP Inc."  # Thay đổi manufacturer
```

### Thay đổi Update Interval

```python
# Update Interval
UPDATE_INTERVAL = 10  # Thay từ 5s thành 10s
```

### Thêm Properties mới

Thêm vào `create_operational_submodel()`:

```python
{
    "idShort": "NetworkTrafficIn",
    "modelType": "Property",
    "valueType": "xs:double",
    "value": "0.0",
    "description": [{"language": "en", "text": "Network traffic in (MB)"}],
    "category": "PARAMETER"
}
```

Và update trong `collect_and_update_operational_data()`:

```python
net_io = psutil.net_io_counters()
network_in_mb = round(net_io.bytes_recv / (1024**2), 2)

updates["NetworkTrafficIn"] = network_in_mb
```

---

## Giám sát nhiều máy tính

### Cách 1: Chạy nhiều instances với Device ID khác nhau

**Máy 1:**
```python
DEVICE_ID = "PC001"
DEVICE_NAME = "Workstation-01"
```

**Máy 2:**
```python
DEVICE_ID = "PC002"
DEVICE_NAME = "Workstation-02"
```

Chạy từng script trên từng máy.

### Cách 2: Tự động detect hostname

Sửa code để tự động lấy Device ID:

```python
import socket
DEVICE_ID = socket.gethostname().upper()  # Dùng hostname làm ID
```

---

## Troubleshooting

### Lỗi: Không kết nối được BaSyx Server

**Nguyên nhân:** Docker containers chưa chạy hoặc port bị chiếm  
**Giải pháp:**
```bash
docker-compose ps  # Kiểm tra status
docker-compose restart  # Restart nếu cần
```

### Lỗi: Update properties failed (500)

**Nguyên nhân:** Format dữ liệu không đúng hoặc MongoDB disconnected  
**Giải pháp:**
```bash
docker logs basyx-environment  # Xem logs
```

Kiểm tra MongoDB connection string trong docker-compose.yml

### Lỗi: AAS already exists (409)

**Nguyên nhân:** AAS đã được tạo trước đó  
**Giải pháp:** Không vấn đề gì! Script tự động detect và skip việc tạo lại

### Data không hiển thị trên UI

**Giải pháp:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Kiểm tra config trong [aas-gui-config.json](aas-gui-config.json)

---

## API Endpoints được sử dụng

### 1. Kiểm tra AAS tồn tại
```http
GET /shells/{base64-encoded-aas-id}
```

### 2. Tạo AAS mới
```http
POST /shells
Content-Type: application/json

{
  "id": "https://example.com/ids/aas/PC001",
  "idShort": "PC001_AAS",
  ...
}
```

### 3. Tạo Submodel
```http
POST /submodels
Content-Type: application/json

{
  "id": "https://example.com/ids/sm/PC001_OperationalData",
  "idShort": "OperationalData",
  ...
}
```

### 4. Link Submodel vào AAS
```http
POST /shells/{base64-encoded-aas-id}/submodel-refs
Content-Type: application/json

{
  "type": "ExternalReference",
  "keys": [{
    "type": "Submodel",
    "value": "https://example.com/ids/sm/PC001_OperationalData"
  }]
}
```

### 5. Update Property Value
```http
GET /submodels/{base64-encoded-sm-id}/submodel-elements/CPUUsage
PUT /submodels/{base64-encoded-sm-id}/submodel-elements/CPUUsage
Content-Type: application/json

{
  "idShort": "CPUUsage",
  "modelType": "Property",
  "valueType": "xs:double",
  "value": "45.3",
  ...
}
```

---

## Best Practices

### 1. Error Handling
Script đã có error handling cho:
- Connection failures
- API errors (404, 500)
- Data collection errors

### 2. Graceful Shutdown
Nhấn Ctrl+C để dừng:
- Tự động cập nhật Status = "Stopped"
- Đóng connections đúng cách

### 3. Monitoring
- Hiển thị real-time metrics trên console
- Log errors rõ ràng
- Success/failure counts

### 4. Data Persistence
- Tất cả updates được lưu vào MongoDB
- Data tồn tại sau khi restart containers
- Historical data có thể query

---

## Kết luận

Script **pc_monitor_integrated.py** cung cấp cách đơn giản nhất để:

✅ Tạo Digital Twin tự động  
✅ Update real-time data  
✅ Persistent storage với MongoDB  
✅ Không cần config phức tạp  

Phù hợp cho:
- Proof of concept
- Development và testing
- Single-machine monitoring
- Learning BaSyx APIs

Để production scale-out với nhiều data sources và protocols phức tạp, nên dùng **DataBridge**.
