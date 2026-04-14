# Hướng dẫn chạy Device Manager Web App

## Giới thiệu
Device Manager là một web application để:
- **Quản lý thiết bị**: Thêm, xóa, xem chi tiết thiết bị
- **Giám sát trạng thái**: Hiển thị thiết bị đang online/offline theo thời gian thực
- **Giả lập thiết bị**: Tạo nhiều thiết bị ảo với dữ liệu giả lập
- **Tích hợp với BaSyx**: Sử dụng API từ Java server

## Cấu trúc hệ thống

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Web Dashboard  │─────▶│  Flask Backend  │─────▶│  BaSyx Server   │
│   (HTML/JS)     │◀─────│    (Python)     │◀─────│    (Java)       │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                            │
                                                            ▼
                                                    ┌─────────────────┐
                                                    │    MongoDB      │
                                                    └─────────────────┘
```

## Yêu cầu hệ thống

- Python 3.8+
- Docker & Docker Compose (cho BaSyx server)
- Các containers Docker đang chạy:
  - basyx-environment (port 8081)
  - mongodb
  - aas-gui (port 3000)

## Cài đặt

### Bước 1: Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

Hoặc cài đặt riêng lẻ:

```bash
pip install Flask Flask-CORS requests psutil
```

### Bước 2: Khởi động Docker containers

```bash
docker-compose up -d
```

Kiểm tra containers đang chạy:

```bash
docker-compose ps
```

## Cách chạy

### 1. Chạy Flask Web App

Mở terminal và chạy:

```bash
python device_manager_web.py
```

Web app sẽ chạy tại: **http://localhost:5000**

### 2. Truy cập Dashboard

Mở browser và truy cập: **http://localhost:5000**

### 3. Giả lập nhiều thiết bị (Optional)

Mở terminal mới và chạy:

```bash
python device_simulator.py
```

Script này sẽ:
- Tạo 5 thiết bị giả lập (SIM001 - SIM005)
- Gửi dữ liệu CPU, RAM, Disk, Network mỗi 10 giây
- Chạy liên tục cho đến khi bấm Ctrl+C

## Tính năng Dashboard

### 📊 Thống kê tổng quan
- Tổng số thiết bị
- Số thiết bị online
- Số thiết bị offline

### 🖥️ Danh sách thiết bị
- Hiển thị thông tin: tên, ID, nhà sản xuất, vị trí
- Trạng thái: Online (màu xanh) / Offline (màu đỏ)
- Thời gian cập nhật lần cuối

### ➕ Thêm thiết bị mới
1. Click nút "Thêm thiết bị mới"
2. Điền thông tin:
   - Device ID (bắt buộc): VD: PC001
   - Tên thiết bị (bắt buộc): VD: Dell Precision 5820
   - Nhà sản xuất: VD: Dell Technologies
   - Vị trí: VD: Workshop Floor 1
3. Click "Thêm thiết bị"

### 🔍 Tìm kiếm
- Tìm kiếm theo ID, tên, nhà sản xuất, vị trí
- Kết quả lọc theo thời gian thực

### 🗑️ Xóa thiết bị
- Click nút "Xóa" trên card thiết bị
- Xác nhận xóa

### 🔄 Làm mới
- Tự động làm mới mỗi 5 giây
- Hoặc click nút "Làm mới" để cập nhật thủ công

### ⚡ Giả lập thiết bị (từ web)
- Click nút "Giả lập thiết bị"
- Hệ thống tự động tạo 5 thiết bị mẫu

## API Endpoints

Flask backend cung cấp các API:

### GET /api/devices
Lấy danh sách tất cả thiết bị

**Response:**
```json
{
  "devices": [
    {
      "id": "PC001",
      "name": "Dell Precision 5820",
      "manufacturer": "Dell Technologies",
      "location": "Workshop Floor 1",
      "status": "online",
      "lastUpdate": "2026-02-04T10:30:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/devices/{device_id}
Lấy thông tin chi tiết một thiết bị

### POST /api/devices
Tạo thiết bị mới

**Request Body:**
```json
{
  "deviceId": "PC001",
  "deviceName": "Dell Precision 5820",
  "manufacturer": "Dell Technologies",
  "location": "Workshop Floor 1"
}
```

### DELETE /api/devices/{device_id}
Xóa thiết bị

## Cơ chế xác định trạng thái Online/Offline

- **Online**: Thiết bị cập nhật dữ liệu trong vòng 60 giây gần nhất
- **Offline**: Thiết bị không cập nhật dữ liệu quá 60 giây
- **Unknown**: Không thể xác định trạng thái

## Cấu trúc dữ liệu trong BaSyx

Mỗi thiết bị có:

### 1. Asset Administration Shell (AAS)
- ID: `https://example.com/ids/aas/{device_id}`
- Metadata về thiết bị

### 2. Nameplate Submodel
- Thông tin cơ bản: Tên, nhà sản xuất, vị trí, serial number

### 3. Technical Data Submodel
- Thông tin kỹ thuật: CPU, RAM, OS

### 4. Operational Data Submodel
- Dữ liệu vận hành theo thời gian thực:
  - CPU Usage
  - Memory Usage
  - Disk Usage
  - Network Sent/Received
  - Timestamp (dùng để xác định online/offline)

## Chạy đồng thời nhiều script

Mở 3 terminal riêng biệt:

**Terminal 1 - Web App:**
```bash
python device_manager_web.py
```

**Terminal 2 - Device Simulator:**
```bash
python device_simulator.py
```

**Terminal 3 - PC Monitor (máy thật):**
```bash
python pc_monitor_integrated.py
```

## Xem dữ liệu chi tiết trong BaSyx

Truy cập BaSyx Web UI: **http://localhost:3000**

Hoặc sử dụng Swagger API: **http://localhost:8081/swagger-ui/index.html**

## Troubleshooting

### Lỗi: Cannot connect to BaSyx server
- Kiểm tra Docker containers đang chạy: `docker-compose ps`
- Khởi động lại containers: `docker-compose restart`

### Lỗi: Port 5000 đã được sử dụng
- Thay đổi port trong file `device_manager_web.py`:
  ```python
  app.run(host='0.0.0.0', port=5001, debug=True)
  ```

### Thiết bị không hiển thị trạng thái online
- Kiểm tra script giả lập hoặc pc_monitor đang chạy
- Xem log của script để đảm bảo dữ liệu được gửi lên

### Không tạo được thiết bị mới
- Kiểm tra MongoDB connection trong docker-compose.yml
- Xem log của basyx-environment: `docker logs basyx-environment`

## Tips & Tricks

1. **Tùy chỉnh interval cập nhật:**
   - Trong `device_manager_web.py`: Sửa `DEVICE_TIMEOUT`
   - Trong `device_simulator.py`: Sửa `UPDATE_INTERVAL`

2. **Thêm nhiều thiết bị giả lập:**
   - Sửa mảng `SIMULATED_DEVICES` trong `device_simulator.py`

3. **Xem API documentation:**
   - Swagger UI: http://localhost:8081/swagger-ui/index.html

4. **Debug mode:**
   - Flask app đã bật debug mode, tự động reload khi sửa code

## Kết luận

Bạn đã có một hệ thống hoàn chỉnh để:
- ✅ Quản lý thiết bị qua web interface
- ✅ Giám sát trạng thái online/offline theo thời gian thực
- ✅ Giả lập nhiều thiết bị với dữ liệu động
- ✅ Tích hợp hoàn toàn với BaSyx Java server API

Enjoy! 🚀
