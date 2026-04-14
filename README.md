# 🏭 Digital Twin System - BaSyx Platform

Hệ thống Digital Twin cho PC/Server Monitoring sử dụng Eclipse BaSyx theo chuẩn Asset Administration Shell (AAS) Industrie 4.0.

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt từ đầu](#-cài-đặt-từ-đầu)
- [Cấu hình](#-cấu-hình)
- [Chạy hệ thống](#-chạy-hệ-thống)
- [Sử dụng](#-sử-dụng)
- [Xử lý sự cố](#-xử-lý-sự-cố)
- [Tài liệu bổ sung](#-tài-liệu-bổ-sung)

---

## 🎯 Giới thiệu

Hệ thống Digital Twin này:

- ✅ Monitor theo dõi trạng thái PC/Server (CPU, RAM, Disk, Network, Temperature)
- ✅ Tuân thủ chuẩn **Asset Administration Shell (AAS) V3** của Industrie 4.0
- ✅ Sử dụng **BaSyx Java Server SDK** và **BaSyx Web UI**
- ✅ Lưu trữ dữ liệu trên **MongoDB Atlas** (Cloud Database)
- ✅ Giao tiếp qua **MQTT** và **REST API**
- ✅ Giao diện web trực quan để quản lý Digital Twin

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    Digital Twin System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │ PC Monitor   │─────▶│ MQTT Broker  │                     │
│  │  (Python)    │      │ (Port 1883)  │                     │
│  └──────────────┘      └──────────────┘                     │
│         │                      │                             │
│         │                      ▼                             │
│         │              ┌──────────────┐                     │
│         └─────────────▶│   BaSyx      │◀──── HTTP/REST     │
│                        │  Environment │                     │
│                        │  (Port 8081) │                     │
│                        └──────────────┘                     │
│                              │                               │
│                              ▼                               │
│                        ┌──────────────┐                     │
│                        │  MongoDB     │                     │
│                        │   Atlas      │                     │
│                        │  (Cloud DB)  │                     │
│                        └──────────────┘                     │
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Web UI     │─────▶│    Nginx     │                     │
│  │ (Port 3000)  │      │ Proxy (8888) │                     │
│  └──────────────┘      └──────────────┘                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Thành phần chính:

1. **MQTT Broker** (Eclipse Mosquitto 1.6)
   - Port 1883 (MQTT), 9001 (WebSocket)
   - Nhận dữ liệu real-time từ sensors/monitors

2. **BaSyx Environment** (All-in-One)
   - AAS Repository - Lưu trữ Asset Administration Shells
   - Submodel Repository - Lưu trữ Submodels
   - Registry - Đăng ký và tìm kiếm AAS
   - ConceptDescription Repository
   - REST API trên Port 8081

3. **MongoDB Atlas**
   - Cloud database lưu trữ persistent data
   - Collections: AAS models, Submodels, Registry entries

4. **BaSyx Web UI**
   - Giao diện web quản lý Digital Twin
   - Port 3000

5. **Nginx Reverse Proxy**
   - Giải quyết CORS issues
   - Port 8888

6. **PC Monitor Script** (Python)
   - Thu thập metrics: CPU, RAM, Disk, Network, Temperature
   - Gửi dữ liệu qua MQTT và REST API
   - Tự động tạo và cập nhật AAS

---

## 💻 Yêu cầu hệ thống

### Phần mềm cần cài đặt

#### 1. **Git**

```powershell
# Kiểm tra đã cài chưa
git --version

# Nếu chưa có, tải từ: https://git-scm.com/download/win
```

#### 2. **Docker Desktop** (Bắt buộc)

```powershell
# Tải từ: https://www.docker.com/products/docker-desktop/

# Sau khi cài, kiểm tra:
docker --version
docker-compose --version
```

**Lưu ý:**

- Bật WSL 2 trên Windows (Docker sẽ hỏi khi cài)
- Docker Desktop phải đang chạy

#### 3. **Python 3.8+**

```powershell
# Kiểm tra
python --version

# Nếu chưa có, tải từ: https://www.python.org/downloads/
# Nhớ chọn "Add Python to PATH" khi cài
```

#### 4. **Java 17** (Nếu muốn build từ source)

```powershell
# Kiểm tra
java -version

# Nếu chưa có, tải từ: https://adoptium.net/
```

#### 5. **Maven** (Nếu muốn build từ source)

```powershell
# Kiểm tra
mvn -version

# Nếu chưa có, tải từ: https://maven.apache.org/download.cgi
```

### Phần cứng khuyến nghị

- **RAM:** 8GB trở lên (16GB khuyến nghị)
- **CPU:** 4 cores trở lên
- **Disk:** 10GB trống (cho Docker images)
- **Internet:** Ổn định (để kết nối MongoDB Atlas)

---

## 🚀 Cài đặt từ đầu

### Bước 1: Clone Repository

```powershell
# Chọn thư mục làm việc
cd C:\Users\YourName\Projects

# Clone repository
git clone https://github.com/your-username/DigitalTwin.git
cd DigitalTwin
```

### Bước 2: Cài đặt Python Dependencies

```powershell
# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
.\venv\Scripts\Activate.ps1

# Cài đặt packages
pip install -r requirements.txt
```

**Nếu chưa có file requirements.txt**, tạo file với nội dung:

```txt
requests>=2.31.0
psutil>=5.9.0
paho-mqtt>=1.6.1
```

Hoặc cài trực tiếp:

```powershell
pip install requests psutil paho-mqtt
```

### Bước 3: Build Docker Images từ Source

#### Option A: Build images (Khuyến nghị - để có version mới nhất)

```powershell
# 1. Build BaSyx Environment (All-in-One)
cd basyx-java-server-sdk-main
docker build -f Dockerfile.environment -t basyx-environment:latest .
cd ..

# 2. Build BaSyx Web UI
cd basyx-aas-web-ui\aas-web-ui
docker build -t basyx-aas-web-ui:local .
cd ..\..
```

**Lưu ý:** Build có thể mất 10-30 phút tùy vào tốc độ máy.

#### Option B: Sử dụng pre-built images từ Docker Hub

Nếu không muốn build, sửa file `docker-compose.yml`:

```yaml
basyx-environment:
  image: eclipsebasyx/aas-environment:2.0.0-SNAPSHOT
  # ... các config khác giữ nguyên

aas-gui:
  image: eclipsebasyx/aas-gui:v2-240703
  # ... các config khác giữ nguyên
```

### Bước 4: Xác nhận Docker Images

```powershell
# Xem danh sách images đã build
docker images | Select-String "basyx"

# Kết quả mong đợi:
# basyx-environment       latest
# basyx-aas-web-ui        local
```

---

## ⚙️ Cấu hình

### 1. Cấu hình MongoDB Atlas

Dự án sử dụng MongoDB Atlas (Cloud Database miễn phí).

#### Nếu dùng MongoDB Atlas có sẵn:

Mở file `docker-compose.yml` và cập nhật:

```yaml
environment:
  - SPRING_DATA_MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/DatabaseName
  - SPRING_DATA_MONGODB_DATABASE=DatabaseName
```

#### Nếu tạo MongoDB Atlas mới:

1. Truy cập: https://www.mongodb.com/cloud/atlas/register
2. Tạo tài khoản miễn phí (FREE Tier M0)
3. Tạo Cluster mới
4. Tạo Database User:
   - Username: `sa`
   - Password: `Admin@123` (hoặc tự chọn)
5. Whitelist IP: Chọn "Allow Access from Anywhere" (0.0.0.0/0)
6. Lấy Connection String:
   - Chọn "Connect Your Application"
   - Copy connection string
   - Thay `<password>` bằng password thực

#### Hoặc dùng MongoDB local:

```yaml
environment:
  - SPRING_DATA_MONGODB_URI=mongodb://mongodb:27017/DigitalTwinDB
```

Và thêm service MongoDB vào `docker-compose.yml`:

```yaml
mongodb:
  image: mongo:7.0
  container_name: mongodb
  ports:
    - "27017:27017"
  volumes:
    - mongodb_data:/data/db

volumes:
  mongodb_data:
```

### 2. Cấu hình PC Monitor Script

Mở file `pc_monitor_integrated.py` và chỉnh sửa:

```python
# BaSyx Server Configuration
BASYX_URL = "http://localhost:8081"  # Giữ nguyên nếu chạy local

# Device Configuration - THAY ĐỔI THEO MÁY CỦA BẠN
DEVICE_ID = "PC001"              # ← Đổi thành ID unique cho máy của bạn
DEVICE_NAME = "Dell Precision"   # ← Tên máy của bạn
LOCATION = "Office Room 301"     # ← Vị trí máy
MANUFACTURER = "Dell"            # ← Hãng sản xuất

# Update Interval
UPDATE_INTERVAL = 5  # Cập nhật mỗi 5 giây (có thể đổi thành 10, 30, 60...)
```

### 3. Cấu hình AAS GUI

File `aas-gui-config.json` đã được cấu hình sẵn. Kiểm tra:

```json
{
  "logo": "Logo_EN_AAS.png",
  "logoPath": "",
  "primaryColor": "#00A651",
  "AASServerURL": "http://localhost:8081",
  "SubmodelRegistryURL": "http://localhost:8081",
  "CDRepositoryURL": "http://localhost:8081",
  "AASDiscoveryURL": "http://localhost:8081",
  "dashboardServiceURL": ""
}
```

---

## 🎮 Chạy hệ thống

### Bước 1: Khởi động Docker Services

```powershell
# Đảm bảo Docker Desktop đang chạy
# Kiểm tra:
docker ps

# Khởi động tất cả services
docker-compose up -d

# Xem logs (Optional - để debug)
docker-compose logs -f
```

**Đợi 30-60 giây** để các services khởi động hoàn toàn.

### Bước 2: Kiểm tra trạng thái

```powershell
# Xem containers đang chạy
docker-compose ps

# Kết quả mong đợi (STATUS = Up):
# NAME                IMAGE                      STATUS
# basyx-environment   basyx-environment:latest   Up
# aas-gui             basyx-aas-web-ui:local     Up
# mqtt-broker         eclipse-mosquitto:1.6      Up
# nginx-proxy         nginx:alpine               Up
```

### Bước 3: Kiểm tra kết nối

```powershell
# Test BaSyx Environment API
curl http://localhost:8081/shells

# Test Nginx Proxy
curl http://localhost:8888/shells

# Kết quả mong đợi: {"result":[],"paging_metadata":{...}}
```

### Bước 4: Truy cập Web UI

Mở trình duyệt và truy cập:

- **Web UI:** http://localhost:3000
- **BaSyx API (qua Nginx):** http://localhost:8888/shells
- **BaSyx API (trực tiếp):** http://localhost:8081/shells

Nếu Web UI hiện **"No AAS available"** → Bình thường, chúng ta sẽ tạo AAS ở bước tiếp theo.

### Bước 5: Chạy PC Monitor

Mở terminal mới (PowerShell):

```powershell
# Đảm bảo đang ở thư mục project
cd C:\Users\YourName\Projects\DigitalTwin

# Kích hoạt virtual environment (nếu dùng)
.\venv\Scripts\Activate.ps1

# Chạy PC Monitor
python pc_monitor_integrated.py
```

**Kết quả mong đợi:**

```
[14:30:15] 🚀 BaSyx PC Monitor v2.0
[14:30:15] 📡 Connecting to BaSyx Environment: http://localhost:8081
[14:30:16] ✅ BaSyx Environment is online!
[14:30:16] 🔍 Checking if AAS exists...
[14:30:16] ⚙️  AAS not found. Creating new AAS...
[14:30:17] ✅ Successfully created AAS: PC001
[14:30:17] ✅ Successfully created Submodel: Nameplate
[14:30:17] ✅ Successfully created Submodel: TechnicalData
[14:30:17] ✅ Successfully created Submodel: OperationalData
[14:30:17] 🎯 Starting monitoring loop...
[14:30:17] Updated 7/7 properties:   CPU: 15.2% | RAM: 62.3% (14.8GB) | Disk: 45.2% (124GB) | Uptime: 48h
[14:30:22] Updated 7/7 properties:   CPU: 12.8% | RAM: 62.5% (14.9GB) | Disk: 45.2% (124GB) | Uptime: 48h
...
```

### Bước 6: Xem Digital Twin trên Web UI

1. Quay lại trình duyệt http://localhost:3000
2. Bấm nút **"Refresh"** hoặc **F5**
3. Bạn sẽ thấy AAS mới xuất hiện với tên máy của bạn
4. Click vào AAS để xem chi tiết:
   - **Nameplate:** Thông tin nhận dạng (tên, ID, nhà sản xuất...)
   - **TechnicalData:** Thông tin phần cứng (CPU, RAM, OS...)
   - **OperationalData:** Dữ liệu real-time (CPU%, RAM%, Disk%, Temperature...)

---

## 📊 Sử dụng

### Giám sát nhiều máy

Để giám sát nhiều máy:

1. **Trên mỗi máy client:**

   ```powershell
   # Clone repository
   git clone https://github.com/your-username/DigitalTwin.git
   cd DigitalTwin

   # Cài dependencies
   pip install requests psutil paho-mqtt

   # Sửa pc_monitor_integrated.py
   # - Đổi DEVICE_ID thành unique ID (PC002, PC003...)
   # - Đổi BASYX_URL thành IP của máy server
   #   VD: BASYX_URL = "http://192.168.1.100:8081"

   # Chạy monitor
   python pc_monitor_integrated.py
   ```

2. **Trên máy server (chạy Docker):**
   - Không cần làm gì thêm
   - Tất cả dữ liệu từ các client sẽ tự động xuất hiện trên Web UI

### REST API Examples

```powershell
# 1. Lấy danh sách tất cả AAS
curl http://localhost:8081/shells

# 2. Lấy chi tiết 1 AAS (cần encode ID)
$aasId = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("https://example.com/ids/aas/PC001"))
curl "http://localhost:8081/shells/$aasId"

# 3. Lấy danh sách Submodels
curl http://localhost:8081/submodels

# 4. Lấy giá trị property cụ thể
curl "http://localhost:8081/submodels/{submodelId}/submodel-elements/CPUUsage"
```

### MQTT Monitoring

```powershell
# Cài MQTT client (Windows)
# Download từ: https://mosquitto.org/download/

# Subscribe to MQTT topics
mosquitto_sub -h localhost -t "dt/pc/#" -v

# Kết quả:
# dt/pc/PC001/cpu 15.2
# dt/pc/PC001/ram 62.3
# dt/pc/PC001/disk 45.2
```

### Xem MongoDB Data

```powershell
# Cài MongoDB Compass: https://www.mongodb.com/try/download/compass

# Connect đến MongoDB Atlas:
# Connection String: mongodb+srv://sa:Admin@123@cluster0.xxx.mongodb.net/

# Xem collections:
# - Database: DigitalTwinDB
#   - aasShell (AAS data)
#   - submodel (Submodel data)
#   - conceptdescription
```

---

## 🔧 Xử lý sự cố

### 1. Docker container không khởi động

```powershell
# Xem logs chi tiết
docker-compose logs basyx-environment

# Thường gặp:
# - Port đã bị chiếm → Đổi port trong docker-compose.yml
# - MongoDB connection failed → Kiểm tra connection string
```

### 2. Lỗi "Cannot connect to BaSyx Environment"

```powershell
# Kiểm tra container có chạy không
docker ps | Select-String basyx

# Kiểm tra logs
docker logs basyx-environment

# Test API trực tiếp
curl http://localhost:8081/shells

# Nếu 404 → OK, service đang chạy nhưng chưa có data
# Nếu không kết nối được → Container chưa khởi động xong, đợi thêm 1-2 phút
```

### 3. Web UI không hiển thị AAS

1. **Kiểm tra config:**

   ```powershell
   # Xem file aas-gui-config.json
   cat aas-gui-config.json

   # Đảm bảo AASServerURL đúng: "http://localhost:8081"
   ```

2. **Clear browser cache:**
   - Ctrl + Shift + Delete
   - Xóa cache và cookies
   - F5 để refresh

3. **Kiểm tra CORS:**

   ```powershell
   # Test qua Nginx proxy (giải quyết CORS)
   curl http://localhost:8888/shells

   # Đổi AASServerURL trong aas-gui-config.json thành:
   # "AASServerURL": "http://localhost:8888"
   ```

### 4. Python script lỗi

```powershell
# Lỗi: ModuleNotFoundError
pip install requests psutil paho-mqtt

# Lỗi: Connection refused
# → Kiểm tra BASYX_URL trong script
# → Đảm bảo Docker containers đang chạy

# Lỗi: "Failed to update property"
# → Bình thường khi AAS chưa được tạo
# → Script sẽ tự động tạo AAS trong lần chạy đầu
```

### 5. MongoDB connection issues

```powershell
# Test MongoDB connection
# Sử dụng MongoDB Compass hoặc:

# PowerShell test
$uri = "mongodb+srv://sa:Admin@123@cluster0.xxx.mongodb.net/"
# Nếu lỗi → Kiểm tra:
# 1. Username/password đúng chưa
# 2. IP đã được whitelist chưa (0.0.0.0/0)
# 3. Connection string có đúng format
```

### 6. Build Docker image failed

```powershell
# Lỗi: Maven build failed
# → Cần Java 17
java -version

# Set Java 17 nếu có nhiều version
.\Huongdan\set_java17.ps1

# Lỗi: Disk space
# → Xóa unused images
docker system prune -a

# Build lại với logs đầy đủ
docker build --no-cache --progress=plain -f Dockerfile.environment -t basyx-environment:latest .
```

### 7. Port conflicts

Nếu port đã bị chiếm, sửa `docker-compose.yml`:

```yaml
# Đổi port bên trái (host port), giữ nguyên port bên phải (container port)
ports:
  - "8082:8081" # BaSyx (đổi từ 8081→8082)
  - "3001:3000" # Web UI (đổi từ 3000→3001)
  - "1884:1883" # MQTT (đổi từ 1883→1884)
```

Nhớ cập nhật lại URLs trong scripts và configs!

---

## 🛑 Dừng hệ thống

### Dừng tạm thời

```powershell
# Dừng tất cả containers (giữ data)
docker-compose stop

# Khởi động lại
docker-compose start
```

### Dừng và xóa containers

```powershell
# Dừng và xóa containers (giữ images và volumes)
docker-compose down

# Khởi động lại từ đầu
docker-compose up -d
```

### Xóa toàn bộ (reset về ban đầu)

```powershell
# Dừng và xóa containers, volumes
docker-compose down -v

# Xóa images (nếu muốn build lại)
docker rmi basyx-environment:latest basyx-aas-web-ui:local

# Build lại từ đầu
docker build -f Dockerfile.environment -t basyx-environment:latest basyx-java-server-sdk-main/
docker build -t basyx-aas-web-ui:local basyx-aas-web-ui/aas-web-ui/
```

---

## 📚 Tài liệu bổ sung

### Trong thư mục `Huongdan/`

- **QUICKSTART.md** - Hướng dẫn nhanh cho người đã setup
- **BUILD_FROM_SOURCE.md** - Hướng dẫn build images chi tiết
- **PC_MONITOR_GUIDE.md** - Hướng dẫn sử dụng PC Monitor
- **DATABRIDGE_RUNNING.md** - Hướng dẫn chạy Data Bridge (MQTT→MongoDB)
- **FIX_MONGODB_CONNECTION.md** - Sửa lỗi kết nối MongoDB
- **DOCUMENTATION.md** - Tài liệu AAS và BaSyx API
- **HUONG_DAN_DAY_DU.md** - Hướng dẫn đầy đủ bằng tiếng Việt

### Resources bên ngoài

- **BaSyx Documentation:** https://wiki.basyx.org/
- **AAS Specification:** https://industrialdigitaltwin.org/
- **BaSyx GitHub:** https://github.com/eclipse-basyx
- **Docker Documentation:** https://docs.docker.com/

---

## 🤝 Đóng góp

Nếu bạn muốn đóng góp vào dự án:

1. Fork repository
2. Tạo branch mới: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add some amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Tạo Pull Request

---

## 📝 License

Dự án này sử dụng Eclipse BaSyx framework, tuân thủ theo [MIT License](LICENSE).

---

## 📞 Liên hệ & Hỗ trợ

- **Issues:** https://github.com/your-username/DigitalTwin/issues
- **Email:** your.email@example.com
- **BaSyx Community:** https://github.com/eclipse-basyx/basyx-java-server-sdk/discussions

---

## ✅ Checklist cho lần đầu setup

- [ ] Cài đặt Docker Desktop
- [ ] Cài đặt Python 3.8+
- [ ] Clone repository
- [ ] Cài đặt Python dependencies (`pip install -r requirements.txt`)
- [ ] Build Docker images (hoặc dùng pre-built)
- [ ] Cấu hình MongoDB connection trong `docker-compose.yml`
- [ ] Chỉnh sửa DEVICE_ID trong `pc_monitor_integrated.py`
- [ ] Chạy `docker-compose up -d`
- [ ] Đợi 30-60 giây
- [ ] Test API: `curl http://localhost:8081/shells`
- [ ] Mở Web UI: http://localhost:3000
- [ ] Chạy `python pc_monitor_integrated.py`
- [ ] Kiểm tra Web UI có hiển thị AAS

**🎉 Chúc bạn thành công!**

# DigitalTwin
