# 🚀 HƯỚNG DẪN NHANH - Digital Twin System

## ✅ Đã hoàn thành

Hệ thống Digital Twin của bạn đã được cấu hình hoàn chỉnh với:

### 🏗️ Kiến trúc
- ✅ **MQTT Broker** (Eclipse Mosquitto) - Port 1883, 9001
- ✅ **AAS Registry** (BaSyx) - Port 4000 + MongoDB Atlas
- ✅ **AAS Server** (BaSyx) - Port 4001 + MongoDB Atlas  
- ✅ **AAS GUI** (Web Interface) - Port 3000
- ✅ **Data Bridge** (Python) - Kết nối MQTT ↔ MongoDB ↔ AAS

### 🗄️ Database
- ✅ Kết nối MongoDB Atlas: `mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB`
- ✅ Database: `DigitalTwinDB`
- ✅ Collections: `sensors_data`, `aas_models`

---

## 🎯 Cách sử dụng

### Bước 1: Khởi động Docker Containers
```powershell
# Cách 1: Dùng script tự động
python start_system.py

# Cách 2: Dùng docker-compose trực tiếp
docker-compose up -d
```

### Bước 2: Khởi động Data Bridge (Terminal riêng)
```powershell
python databridge.py
```
Data Bridge sẽ lắng nghe MQTT và lưu dữ liệu vào MongoDB Atlas

### Bước 3: Gửi dữ liệu test (Terminal riêng)
```powershell
python pc_simulator.py
```
Simulator sẽ gửi dữ liệu giả lập về CPU, RAM, Disk

---

## 🌐 Truy cập các dịch vụ

| Dịch vụ | URL | Mô tả |
|---------|-----|-------|
| **AAS GUI** | http://localhost:3000 | Giao diện web quản lý Digital Twin |
| **AAS Server API** | http://localhost:4001/aas-server | REST API của AAS Server |
| **AAS Registry API** | http://localhost:4000/registry | REST API của AAS Registry |
| **MQTT Broker** | mqtt://localhost:1883 | MQTT protocol |
| **MongoDB Atlas** | Cloud | Truy cập qua MongoDB Compass hoặc Atlas UI |

---

## 📊 Kiểm tra hệ thống

### Xem trạng thái containers
```powershell
docker-compose ps
```

### Xem logs
```powershell
# Tất cả containers
docker-compose logs -f

# Container cụ thể
docker-compose logs -f aas-server
docker-compose logs -f mqtt-broker
```

### Test MQTT
```powershell
# Publish test message (cần cài mosquitto-clients)
mosquitto_pub -h localhost -t "dt/sensors/test" -m '{"test": "hello"}'

# Subscribe để xem messages
mosquitto_sub -h localhost -t "dt/sensors/#"
```

---

## 🛑 Dừng hệ thống

```powershell
# Cách 1: Dùng script
python stop_system.py

# Cách 2: Dùng docker-compose
docker-compose down

# Dừng và xóa volumes
docker-compose down -v
```

---

## 📂 Cấu trúc dữ liệu MQTT

### Topic format
```
dt/sensors/{device_id}/{sensor_type}
```

### Ví dụ messages
**Topic**: `dt/sensors/pc01/cpu`
```json
{
  "device_id": "pc01",
  "cpu_usage": 45.2,
  "ram_usage": 60.1,
  "disk_usage": 70.5,
  "timestamp": "2026-01-01T10:30:00"
}
```

---

## 🔧 Troubleshooting

### ❌ Lỗi: Cannot connect to MongoDB
**Giải pháp:**
1. Kiểm tra connection string trong `docker-compose.yml` và `databridge.py`
2. Kiểm tra Network Access trên MongoDB Atlas (whitelist IP)
3. Kiểm tra username/password

### ❌ Lỗi: Container không khởi động
**Giải pháp:**
```powershell
# Xem logs chi tiết
docker-compose logs [container_name]

# Restart container
docker-compose restart [container_name]

# Rebuild (nếu cần)
docker-compose up -d --force-recreate
```

### ❌ Lỗi: MQTT không nhận dữ liệu
**Giải pháp:**
1. Kiểm tra MQTT Broker đang chạy: `docker ps | findstr mqtt`
2. Kiểm tra Data Bridge đang chạy
3. Kiểm tra topic đang subscribe đúng: `dt/sensors/#`

### ❌ Lỗi: Port đã được sử dụng
**Giải pháp:**
```powershell
# Tìm process đang dùng port
netstat -ano | findstr :3000
netstat -ano | findstr :4001

# Kill process (thay PID)
taskkill /PID <PID> /F
```

---

## 📚 Files trong project

| File | Mô tả |
|------|-------|
| `docker-compose.yml` | Cấu hình các containers |
| `databridge.py` | Data Bridge kết nối MQTT → MongoDB → AAS |
| `pc_simulator.py` | Simulator gửi dữ liệu test |
| `start_system.py` | Script khởi động tự động |
| `stop_system.py` | Script dừng hệ thống |
| `README.md` | Tài liệu chi tiết (English) |
| `QUICKSTART.md` | Hướng dẫn này |
| `.env.example` | Template file cấu hình |

---

## 🎓 Tài nguyên học thêm

- [Eclipse BaSyx Documentation](https://wiki.eclipse.org/BaSyx)
- [MongoDB Atlas Docs](https://docs.atlas.mongodb.com/)
- [MQTT Protocol](https://mqtt.org/)
- [Digital Twin Concepts](https://en.wikipedia.org/wiki/Digital_twin)

---

## 💡 Tips

1. **Monitoring**: Sử dụng MongoDB Compass để xem dữ liệu realtime
2. **Testing**: Dùng MQTT Explorer để test publish/subscribe
3. **Debugging**: Enable verbose logging trong `databridge.py`
4. **Production**: Thay đổi credentials và sử dụng environment variables

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Docker đã chạy chưa
2. MongoDB Atlas connection string đúng chưa
3. Port có bị conflict không
4. Logs của từng container

**Chúc bạn thành công! 🎉**
