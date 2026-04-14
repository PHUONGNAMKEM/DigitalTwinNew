# ✅ DATABRIDGE ĐÃ CHẠY ĐƯỢC!

## ✔️ Kết quả hiện tại

Data Bridge đã khởi động thành công và đang hoạt động:

```
============================================================
BaSyx Data Bridge dang khoi dong...
============================================================
OK - Da ket noi MQTT Broker: localhost:1883
OK - Da subscribe: industry/pc/+/telemetry
OK - Da subscribe: industry/pc/+/status
OK - Da subscribe: industry/pc/+/heartbeat
```

**✅ MQTT đang hoạt động bình thường!**

---

## ⚠️ LƯU Ý VỀ MONGODB

### Lỗi hiện tại:
```
LOI - Loi ket noi MongoDB: The DNS response does not contain an answer to the question: _mongodb._tcp.cluster0.wrpp0cf.mongodb.net. IN SRV
```

### Nguyên nhân:
Connection string không đúng hoặc cluster không tồn tại.

### Giải pháp:

#### **Bước 1: Lấy Connection String thật từ MongoDB Atlas**

1. Đăng nhập: https://cloud.mongodb.com
2. Chọn cluster của bạn
3. Click nút **"Connect"**
4. Chọn **"Connect your application"**
5. Chọn Driver: **Python**, Version: **3.12 or later**
6. Copy connection string

**Ví dụ:**
```
mongodb+srv://<username>:<password>@<cluster-name>.<id>.mongodb.net/<database>
```

#### **Bước 2: Cập nhật trong file databridge.py**

Mở file [databridge.py](databridge.py), dòng 21:

```python
# THAY ĐỔI DÒNG NÀY:
MONGODB_URI = "mongodb+srv://sa:Admin%40123@cluster0.wrpp0cf.mongodb.net/DigitalTwinDB"

# THÀNH connection string thật của bạn:
MONGODB_URI = "mongodb+srv://<username>:<password>@<cluster-real>.mongodb.net/DigitalTwinDB"
```

**Lưu ý:** Nếu password có ký tự đặc biệt, phải encode:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`

Xem chi tiết: [FIX_MONGODB_CONNECTION.md](FIX_MONGODB_CONNECTION.md)

#### **Bước 3: Restart Data Bridge**

```powershell
# Nhấn Ctrl+C để stop
# Chạy lại:
python databridge.py
```

---

## ⚠️ DEPRECATION WARNING (Không quan trọng)

### Warning hiện tại:
```
DeprecationWarning: Callback API version 1 is deprecated, update to latest version
```

### Giải pháp (Tùy chọn):

Nếu muốn loại bỏ warning này, sửa dòng 77 trong databridge.py:

**Cũ:**
```python
self.mqtt_client = mqtt.Client(client_id="databridge")
```

**Mới:**
```python
self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="databridge")
```

**Hoặc không cần sửa** - vẫn hoạt động bình thường!

---

## 🎯 TIẾP THEO: CHẠY PC MONITOR

Data Bridge đã sẵn sàng nhận dữ liệu! Bây giờ mở **Terminal thứ 2** và chạy:

```powershell
python pc_monitor.py
```

PC Monitor sẽ:
1. Thu thập dữ liệu CPU, RAM, Disk
2. Gửi qua MQTT tới Data Bridge
3. Data Bridge sẽ hiển thị:
   ```
   [{time}] Telemetry from PC001:
      CPU: 45.2% | RAM: 60.1% | Disk: 70.5%
   ```

---

## 📊 KIỂM TRA HỆ THỐNG

### Kiểm tra MQTT Broker
```powershell
docker ps | findstr mqtt
```

Output mong muốn:
```
mqtt-broker   Up   0.0.0.0:1883->1883/tcp
```

### Kiểm tra Data Bridge đang chạy
Xem terminal có output:
```
Dang cho du lieu tu MQTT...
OK - Da ket noi MQTT Broker: localhost:1883
```

### Test gửi message thử
```powershell
# Cài mosquitto-clients nếu chưa có
# Gửi test message:
mosquitto_pub -h localhost -t "industry/pc/TEST/telemetry" -m '{"device_id":"TEST","cpu_usage":50}'
```

Data Bridge sẽ hiển thị:
```
[10:30:00] Telemetry from TEST:
   CPU: 50% | RAM: 0% | Disk: 0%
```

---

## ✅ TÓM TẮT

**Hiện tại:**
- ✅ Data Bridge đã chạy
- ✅ MQTT Broker đã kết nối
- ✅ Đang chờ dữ liệu từ PC Monitor
- ⚠️ MongoDB chưa kết nối (nhưng không ảnh hưởng test)

**Để hoàn thiện:**
1. Cập nhật MongoDB connection string thật
2. Chạy `python pc_monitor.py` ở terminal khác
3. Xem dữ liệu realtime

**Đã thành công phần lớn! 🎉**

---

## 🆘 NẾU GẶP VẤN ĐỀ

### Data Bridge không kết nối MQTT
```powershell
# Kiểm tra MQTT Broker
docker-compose ps
docker-compose logs mqtt-broker

# Restart MQTT Broker
docker-compose restart mqtt-broker
```

### Port 1883 bị chiếm
```powershell
# Tìm process đang dùng port
netstat -ano | findstr :1883

# Kill process (thay <PID>)
taskkill /PID <PID> /F
```

### Muốn dừng Data Bridge
```
Nhấn Ctrl+C trong terminal
```

Output:
```
Dang dung Data Bridge...
OK - Data Bridge da dung
```
