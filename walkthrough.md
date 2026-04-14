# Hướng dẫn Deploy Digital Twin (Tổng hợp)

Tài liệu này tổng hợp lại toàn bộ quá trình và cấu hình đã thực hiện để deploy hoàn chỉnh dự án Digital Twin lên server Linux Ubuntu ([digitaltwin.wisdombrain.org](file:///tmp/digitaltwin.wisdombrain.org) và [digitaltwinui.wisdombrain.org](file:///tmp/digitaltwinui.wisdombrain.org)) thông qua Cloudflare Tunnel.

---

## 1. Môi trường hệ thống
- **Server**: Linux (Ubuntu)
- **Cơ sở dữ liệu**: MongoDB Atlas
- **Network Expose**: Cloudflare Tunnel (Tunnel Name: `coursejava`)
- **Main App Domain**: [digitaltwin.wisdombrain.org](file:///tmp/digitaltwin.wisdombrain.org) (Giao diện chính - Eclipse BaSyx UI)
- **Device Manager Domain**: [digitaltwinui.wisdombrain.org](file:///tmp/digitaltwinui.wisdombrain.org) (Giao diện phụ - Flask App)

---

## 2. Docker & Eclipse BaSyx Environment

### 2.1 Cấu hình [docker-compose.yml](file:///home/ubuntu/Downloads/DigitalTwin-main/docker-compose.yml)
Chỉnh sửa file [docker-compose.yml](file:///home/ubuntu/Downloads/DigitalTwin-main/docker-compose.yml) tại `/home/ubuntu/Downloads/DigitalTwin-main`:
- Cập nhật `aas-gui` port host thành `3001` (tránh xung đột với Kubernetes đang dùng port `3000`).
- Thay vì tự build `basyx-environment` từ thư mục source đang bị rỗng/lỗi, hãy dùng **official pre-built image** từ Docker Hub (đảm bảo tính ổn định với Spring Data MongoDB).

```yaml
  basyx-environment:
    image: eclipsebasyx/aas-environment:2.0.0-SNAPSHOT
    container_name: basyx-environment
    ports:
      - "8081:8081"
    restart: unless-stopped

  aas-gui:
    image: eclipsebasyx/aas-gui:v2-250417
    container_name: aas-gui
    ports:
      - "3001:3000"  # Đổi port từ 3000 qua 3001
    restart: unless-stopped
```

### 2.2 Fixing Nginx Proxy nội bộ (cho Docker)
File `nginx.conf` (`/home/ubuntu/Downloads/DigitalTwin-main/nginx.conf`) proxy port `8888`. Cần loại bỏ các service cũ (`aas-registry`, `aas-server`) của bản v1 và trỏ về chuẩn `basyx-environment` v2 (All-in-One).

```nginx
        # Proxy all API endpoints to BaSyx Environment (All-in-One)
        location / {
            proxy_pass http://basyx-environment:8081;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
```

### 2.3 Khởi động Docker Service
```bash
cd /home/ubuntu/Downloads/DigitalTwin-main
docker compose up -d
```
Tất cả chạy thành công vởi 4 services: `basyx-environment`, `aas-gui`, `mqtt-broker`, `nginx-proxy`.

---

## 3. Cấu hình Domain Chính (`digitaltwin.wisdombrain.org`)

### 3.1 Cập nhật Endpoint giao diện AAS GUI
Sửa file `/home/ubuntu/Downloads/DigitalTwin-main/aas-gui-config.json`:
```json
{
  "aasRepoPath": "https://digitaltwin.wisdombrain.org/shells",
  "submodelRepoPath": "https://digitaltwin.wisdombrain.org/submodels",
  "cdRepoPath": "https://digitaltwin.wisdombrain.org/concept-descriptions",
  "primaryColor": "#00A651"
}
```

### 3.2 Cấu hình Nginx (`/etc/nginx/sites-available/digitaltwin.wisdombrain.org`)
Cấu hình routing traffic: `/` chuyển cho UI (port `3001`), `/shells` (và các api khác) chuyển cho BaSyx API (`8081`).

```nginx
server {
    listen 80;
    server_name digitaltwin.wisdombrain.org;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /shells {
        proxy_pass http://127.0.0.1:8081/shells;
    }
    # (Tương tự cho /submodels và /concept-descriptions)
}
```

Tạo symlink và reload nginx:
```bash
sudo ln -sf /etc/nginx/sites-available/digitaltwin.wisdombrain.org /etc/nginx/sites-enabled/digitaltwin.wisdombrain.org
sudo nginx -t && sudo systemctl reload nginx
```

---

## 4. Cấu hình Device Manager Web (`digitaltwinui.wisdombrain.org`)

Giao diện quản lý phụ là ứng dụng Flask (`device_manager_web.py`). Hoạt động trên port `5000`.

### 4.1 Tạo Systemd Service với Gunicorn
Cài đặt `gunicorn` trong virtual environment. Tạo file `/etc/systemd/system/device-manager.service`:

```ini
[Unit]
Description=Device Manager Web (Flask)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Downloads/DigitalTwin-main
Environment="PATH=/home/ubuntu/Downloads/DigitalTwin-main/venv/bin"
ExecStart=/home/ubuntu/Downloads/DigitalTwin-main/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 device_manager_web:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Kích hoạt service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now device-manager.service
```

### 4.2 Cấu hình Nginx (`/etc/nginx/sites-available/digitaltwinui.wisdombrain.org`)
Tiếp nhận domain thứ 2 và trỏ về app Flask.

```nginx
server {
    listen 80;
    server_name digitaltwinui.wisdombrain.org;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Reload Nginx lần nữa.

---

## 5. Cấu hình Cloudflare Tunnel Trực Tiếp

Public hai domain mới này lên Internet qua Cloudflared đang chạy ở server.
Sửa `/etc/cloudflared/config.yml` (Thêm sát góc trên của tag `# ===== fallback =====`):

```yaml
ingress:
  - hostname: digitaltwin.wisdombrain.org
    service: http://127.0.0.1:80
  - hostname: digitaltwinui.wisdombrain.org
    service: http://127.0.0.1:80
  # ===== fallback =====
  - service: http_status:404
```

Restart Cloudflare Tunnel:
```bash
sudo systemctl restart cloudflared
```

---

## 6. Khởi động Client Sensor (Python Monitoring)

Tiến hành cài môi trường Python và chạy PC Monitor script để đẩy dữ liệu giả lập (CPU/RAM/Disk) tới server tự động:

```bash
cd /home/ubuntu/Downloads/DigitalTwin-main
sudo apt install python3.12-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Chạy background hoặc sử dụng pm2, nohup để giữ script không tắt
python3 pc_monitor_integrated.py
```
*(Script này gọi API tới `localhost:8081` để tự động khởi tạo Asset Administration Shell và Operational Submodels).*

---

**Quá trình hoàn tất!**
Hai domain đều truy cập thành công và server thu thập dữ liệu PC đang chạy 100% tài nguyên và lưu trữ ngầm tại MongoDB.
