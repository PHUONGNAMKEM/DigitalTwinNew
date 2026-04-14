# 📖 TÀI LIỆU CHI TIẾT - HỆ THỐNG DIGITAL TWIN

## Tác giả: [Tên của bạn]
## Ngày: 01/01/2026
## Version: 1.0

---

# PHẦN 1: KIẾN TRÚC VÀ LUỒNG DỮ LIỆU

## 1.1 Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────┐
│                    MÁY TÍNH VẬT LÝ (Physical Asset)         │
│  - CPU Usage, RAM Usage, Disk Usage                         │
│  - Trạng thái: Online/Offline                               │
└────────────────┬────────────────────────────────────────────┘
                 │ Đọc thông tin hệ thống
                 │ (psutil library)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              PC MONITOR SCRIPT (pc_monitor.py)              │
│  Thu thập: CPU, RAM, Disk, Status                           │
│  Format: JSON                                               │
└────────────────┬────────────────────────────────────────────┘
                 │ Publish qua MQTT
                 │ Topic: industry/pc/{pc_id}/telemetry
                 │        industry/pc/{pc_id}/status
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                 MQTT BROKER (Eclipse Mosquitto)             │
│  Port: 1883 (MQTT), 9001 (WebSocket)                        │
│  Docker Container: mqtt-broker                              │
└──────┬──────────────────────────────────────────────────────┘
       │ Subscribe tất cả topics
       │ Pattern: industry/pc/#
       ▼
┌─────────────────────────────────────────────────────────────┐
│                DATA BRIDGE (databridge.py)                  │
│  - Nhận dữ liệu từ MQTT                                     │
│  - Transform & Validate                                     │
│  - Lưu vào MongoDB Atlas                                    │
│  - Cập nhật AAS Model                                       │
└──────┬─────────────────────┬────────────────────────────────┘
       │                     │
       │                     │ Update AAS Model
       ▼                     ▼
┌──────────────────┐   ┌─────────────────────────────────────┐
│  MONGODB ATLAS   │   │      BASYX AAS FRAMEWORK            │
│  (Cloud DB)      │   │                                     │
│                  │   │  ┌──────────────────────────────┐   │
│  Collections:    │   │  │    AAS Server (4001)         │   │
│  - telemetry     │   │  │  Lưu Asset Administration    │   │
│  - pc_status     │   │  │  Shell Models                │   │
│  - aas_models    │   │  └──────────┬───────────────────┘   │
│  - events        │   │             │                       │
└──────────────────┘   │  ┌──────────▼───────────────────┐   │
                       │  │   AAS Registry (4000)        │   │
                       │  │  Danh bạ các AAS             │   │
                       │  └──────────┬───────────────────┘   │
                       │             │                       │
                       │  ┌──────────▼───────────────────┐   │
                       │  │     AAS GUI (3000)           │   │
                       │  │  Giao diện Web quản lý       │   │
                       │  └──────────────────────────────┘   │
                       └─────────────────────────────────────┘
```

---

# PHẦN 2: CẤU HÌNH KẾT NỐI MONGODB ATLAS

## 2.1 Thay đổi trong docker-compose.yml

### ❓ TẠI SAO PHẢI KẾT NỐI MONGODB ATLAS?

- **Lưu trữ lâu dài**: Dữ liệu không bị mất khi restart container
- **Cloud-based**: Truy cập từ mọi nơi
- **Scalable**: Tự động mở rộng khi cần
- **Backup tự động**: MongoDB Atlas có backup hàng ngày

### 📝 CÁC THAY ĐỔI CỤ THỂ:

#### **Service: aas-registry**

**TRƯỚC KHI THAY ĐỔI:**
```yaml
aas-registry:
  image: eclipsebasyx/aas-registry:1.4.0
  container_name: aas-registry
  ports:
    - "4000:4000"
  environment:
    - BASYX_REGISTRY_PATH=registry
```

**SAU KHI THAY ĐỔI:**
```yaml
aas-registry:
  image: eclipsebasyx/aas-registry:1.4.0
  container_name: aas-registry
  ports:
    - "4000:4000"
  environment:
    - BASYX_REGISTRY_PATH=registry
    - BASYX_BACKEND=MongoDB                    # ← THÊM: Sử dụng MongoDB làm backend
    - BASYX_MONGODB_DBNAME=DigitalTwinDB       # ← THÊM: Tên database
    - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB  # ← THÊM: Connection string
```

**GIẢI THÍCH:**
- `BASYX_BACKEND=MongoDB`: Chuyển từ lưu trữ InMemory (RAM) sang MongoDB
- `BASYX_MONGODB_DBNAME`: Tên database trên MongoDB Atlas
- `BASYX_MONGODB_CONNECTIONURL`: Chuỗi kết nối đầy đủ

#### **Service: aas-server**

**TRƯỚC KHI THAY ĐỔI:**
```yaml
aas-server:
  image: eclipsebasyx/aas-server:1.4.0
  container_name: aas-server
  ports:
    - "4001:4001"
  environment:
    - BASYX_SERVER_PATH=aas-server
  depends_on:
    - aas-registry
```

**SAU KHI THAY ĐỔI:**
```yaml
aas-server:
  image: eclipsebasyx/aas-server:1.4.0
  container_name: aas-server
  ports:
    - "4001:4001"
  environment:
    - BASYX_SERVER_PATH=aas-server
    - BASYX_BACKEND=MongoDB                    # ← THÊM
    - BASYX_MONGODB_DBNAME=DigitalTwinDB       # ← THÊM
    - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB  # ← THÊM
  depends_on:
    - aas-registry
```

### 🔐 ĐỊNH DẠNG CONNECTION STRING

```
mongodb+srv://<username>:<password>@<cluster>.<id>.mongodb.net/<database>
```

**Ví dụ thực tế của bạn:**
```
mongodb+srv://sa:Admin@123@cluster0.wrpp0cf.mongodb.net/DigitalTwinDB
```

**Phân tích:**
- `mongodb+srv://` - Protocol (SRV record)
- `sa` - Username
- `Admin@123` - Password (cần encode nếu có ký tự đặc biệt)
- `cluster0.wrpp0cf.mongodb.net` - Cluster hostname
- `DigitalTwinDB` - Database name

---

# PHẦN 3: FILE DATABRIDGE.PY - CẦU NỐI DỮ LIỆU

## 3.1 Mục đích của Data Bridge

Data Bridge là **cầu nối trung tâm** của hệ thống, thực hiện các nhiệm vụ:

1. **Thu thập dữ liệu** từ MQTT Broker
2. **Xử lý và validate** dữ liệu
3. **Lưu trữ** vào MongoDB Atlas
4. **Cập nhật** AAS Models trong BaSyx
5. **Trigger events** khi có thay đổi quan trọng

## 3.2 Cấu trúc file databridge.py

### **A. Import các thư viện**

```python
import paho.mqtt.client as mqtt  # Thư viện MQTT client
import time
import json
from datetime import datetime
from pymongo import MongoClient   # Thư viện kết nối MongoDB
import requests                   # Thư viện HTTP để gọi AAS APIs
```

### **B. Cấu hình kết nối**

```python
# MongoDB Atlas - Cloud Database
MONGODB_URI = "mongodb+srv://sa:Admin@123@cluster0.wrpp0cf.mongodb.net/DigitalTwinDB"
DB_NAME = "DigitalTwinDB"

# MQTT Broker - Message Queue
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "industry/pc/#"  # Subscribe tất cả topics bắt đầu bằng industry/pc/

# BaSyx AAS Framework
AAS_SERVER_URL = "http://localhost:4001/aas-server"
AAS_REGISTRY_URL = "http://localhost:4000/registry"
```

### **C. Class DataBridge - Các phương thức chính**

#### **1. __init__() - Khởi tạo**

```python
def __init__(self):
    # Kết nối MongoDB Atlas
    self.mongo_client = MongoClient(MONGODB_URI)
    self.db = self.mongo_client[DB_NAME]
    
    # Tạo các collections
    self.telemetry_collection = self.db["telemetry_history"]
    self.status_collection = self.db["pc_status"]
    self.aas_collection = self.db["aas_models"]
    self.events_collection = self.db["events"]
    
    # Setup MQTT Client
    self.mqtt_client = mqtt.Client(client_id="databridge")
    self.mqtt_client.on_connect = self.on_connect
    self.mqtt_client.on_message = self.on_message
```

**GIẢI THÍCH:**
- Tạo kết nối tới MongoDB Atlas
- Khởi tạo 4 collections để lưu các loại dữ liệu khác nhau
- Setup MQTT client với callback functions

#### **2. on_connect() - Callback khi kết nối MQTT**

```python
def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Đã kết nối MQTT Broker")
        client.subscribe("industry/pc/#")  # Subscribe tất cả PC topics
        print(f"✓ Đã subscribe: industry/pc/#")
```

**GIẢI THÍCH:**
- Được gọi tự động khi kết nối MQTT thành công
- Subscribe topic pattern `industry/pc/#` để nhận tất cả messages từ các PC

#### **3. on_message() - Xử lý message từ MQTT**

```python
def on_message(self, client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    # Parse JSON
    data = json.loads(payload)
    data['timestamp'] = datetime.now()
    data['topic'] = topic
    
    # Phân loại và lưu trữ
    if '/telemetry' in topic:
        self.save_telemetry(data)
    elif '/status' in topic:
        self.save_status(data)
    
    # Cập nhật AAS Model
    self.update_aas_model(data)
```

**GIẢI THÍCH:**
- Nhận message từ MQTT
- Parse JSON data
- Phân loại theo topic (telemetry hoặc status)
- Lưu vào MongoDB
- Cập nhật AAS model

---

# PHẦN 4: GIÁM SÁT TRẠNG THÁI MÁY TÍNH

## 4.1 Cấu trúc dữ liệu

### **Collection: telemetry_history**

Lưu trữ lịch sử các thông số kỹ thuật:

```json
{
  "_id": ObjectId("..."),
  "device_id": "PC001",
  "timestamp": ISODate("2026-01-01T10:30:00Z"),
  "cpu_usage": 45.2,
  "cpu_temp": 55.0,
  "ram_usage": 60.1,
  "ram_total": 16384,
  "ram_used": 9830,
  "disk_usage": 70.5,
  "disk_total": 512000,
  "disk_used": 360960,
  "network_sent": 1234567,
  "network_recv": 9876543,
  "topic": "industry/pc/PC001/telemetry"
}
```

### **Collection: pc_status**

Lưu trạng thái hiện tại của từng PC:

```json
{
  "_id": ObjectId("..."),
  "device_id": "PC001",
  "status": "online",  // hoặc "offline"
  "last_seen": ISODate("2026-01-01T10:30:00Z"),
  "uptime": 86400,  // seconds
  "ip_address": "192.168.1.100",
  "hostname": "WORKSTATION-01",
  "os": "Windows 11",
  "location": "Workshop Floor 1"
}
```

### **Collection: aas_models**

Lưu Asset Administration Shell Model:

```json
{
  "_id": ObjectId("..."),
  "aas_id": "PC001_AAS",
  "device_id": "PC001",
  "identification": {
    "id": "https://example.com/ids/aas/PC001",
    "idType": "IRI"
  },
  "asset": {
    "identification": {
      "id": "https://example.com/ids/asset/PC001",
      "idType": "IRI"
    },
    "kind": "Instance"
  },
  "submodels": [
    {
      "identification": {
        "id": "https://example.com/ids/sm/PC001/TechnicalData",
        "idType": "IRI"
      },
      "properties": {
        "cpu_usage": 45.2,
        "ram_usage": 60.1,
        "disk_usage": 70.5,
        "status": "online"
      }
    }
  ],
  "last_update": ISODate("2026-01-01T10:30:00Z")
}
```

### **Collection: events**

Lưu các sự kiện quan trọng:

```json
{
  "_id": ObjectId("..."),
  "device_id": "PC001",
  "event_type": "status_change",
  "event_data": {
    "old_status": "online",
    "new_status": "offline"
  },
  "severity": "warning",  // info, warning, critical
  "timestamp": ISODate("2026-01-01T10:30:00Z"),
  "description": "PC001 went offline"
}
```

---

# PHẦN 5: LUỒNG DỮ LIỆU CHI TIẾT

## 5.1 Luồng Telemetry (Dữ liệu thông số kỹ thuật)

```
1. PC Monitor Script (pc_monitor.py)
   ↓ Đọc thông tin hệ thống (mỗi 5 giây)
   ↓ CPU: 45.2%, RAM: 60.1%, Disk: 70.5%
   ↓
2. Format thành JSON
   {
     "device_id": "PC001",
     "cpu_usage": 45.2,
     "ram_usage": 60.1,
     "disk_usage": 70.5
   }
   ↓
3. Publish MQTT
   Topic: industry/pc/PC001/telemetry
   ↓
4. MQTT Broker nhận và forward
   ↓
5. Data Bridge subscribe và nhận
   ↓
6. Lưu vào MongoDB Atlas
   Collection: telemetry_history
   ↓
7. Cập nhật AAS Model
   Submodel: TechnicalData
   Properties: cpu_usage, ram_usage, disk_usage
```

## 5.2 Luồng Status (Trạng thái Online/Offline)

```
1. PC Monitor Script
   ↓ Khi khởi động
   ↓
2. Publish "online"
   Topic: industry/pc/PC001/status
   Payload: "online"
   QoS: 1 (At least once)
   Retain: True (Lưu message cuối cùng)
   ↓
3. Setup Last Will Message
   Nếu mất kết nối đột ngột
   → MQTT Broker tự động publish "offline"
   ↓
4. Data Bridge nhận status
   ↓
5. Lưu vào MongoDB
   Collection: pc_status
   Update status và last_seen
   ↓
6. Tạo Event (nếu status thay đổi)
   Collection: events
   {
     "event_type": "status_change",
     "old_status": "online",
     "new_status": "offline"
   }
   ↓
7. Cập nhật AAS Model
   Submodel: Status
   Property: operational_status = "offline"
```

---

# PHẦN 6: TẠO AAS MODEL CHO MÁY TÍNH

## 6.1 Cấu trúc AAS cho PC Monitoring

```json
{
  "aasId": "PC001_AAS",
  "identification": {
    "id": "https://digitaltwin.example.com/aas/PC001",
    "idType": "IRI"
  },
  "idShort": "PC001_WorkstationAAS",
  "asset": {
    "identification": {
      "id": "https://digitaltwin.example.com/asset/PC001",
      "idType": "IRI"
    },
    "idShort": "PC001_Asset",
    "kind": "Instance",
    "description": [
      {
        "language": "en",
        "text": "Workstation PC for Digital Twin Monitoring"
      }
    ]
  },
  "submodels": [
    {
      "identification": {
        "id": "https://digitaltwin.example.com/sm/PC001/Identification",
        "idType": "IRI"
      },
      "idShort": "Identification",
      "kind": "Instance",
      "submodelElements": [
        {
          "idShort": "DeviceID",
          "modelType": "Property",
          "valueType": "string",
          "value": "PC001"
        },
        {
          "idShort": "Manufacturer",
          "modelType": "Property",
          "valueType": "string",
          "value": "Dell"
        },
        {
          "idShort": "Model",
          "modelType": "Property",
          "valueType": "string",
          "value": "Precision 7920"
        }
      ]
    },
    {
      "identification": {
        "id": "https://digitaltwin.example.com/sm/PC001/TechnicalData",
        "idType": "IRI"
      },
      "idShort": "TechnicalData",
      "kind": "Instance",
      "submodelElements": [
        {
          "idShort": "CPU_Usage",
          "modelType": "Property",
          "valueType": "double",
          "value": "45.2",
          "unit": "percent"
        },
        {
          "idShort": "RAM_Usage",
          "modelType": "Property",
          "valueType": "double",
          "value": "60.1",
          "unit": "percent"
        },
        {
          "idShort": "Disk_Usage",
          "modelType": "Property",
          "valueType": "double",
          "value": "70.5",
          "unit": "percent"
        }
      ]
    },
    {
      "identification": {
        "id": "https://digitaltwin.example.com/sm/PC001/OperationalData",
        "idType": "IRI"
      },
      "idShort": "OperationalData",
      "kind": "Instance",
      "submodelElements": [
        {
          "idShort": "Status",
          "modelType": "Property",
          "valueType": "string",
          "value": "online"
        },
        {
          "idShort": "Uptime",
          "modelType": "Property",
          "valueType": "integer",
          "value": "86400",
          "unit": "seconds"
        },
        {
          "idShort": "LastSeen",
          "modelType": "Property",
          "valueType": "dateTime",
          "value": "2026-01-01T10:30:00Z"
        }
      ]
    }
  ]
}
```

---

# PHẦN 7: CODE SCRIPTS CHI TIẾT

Tôi sẽ tạo các file scripts mới ở bước tiếp theo để bạn có thể:
1. Monitor PC realtime
2. Tự động tạo AAS models
3. Dashboard hiển thị status
4. Alert khi PC offline

Bạn có muốn tôi tiếp tục tạo các file code này không?
