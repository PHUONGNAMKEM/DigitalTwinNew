# 🔨 Build BaSyx từ Source Code

## 📦 Các Source đã clone

Bạn đã clone 3 repo BaSyx:
1. **basyx-aas-web-ui/** - Giao diện Web UI
2. **basyx-java-server-sdk/** - AAS Server & Registry
3. **basyx-applications/** - Các ứng dụng mở rộng

## 🏗️ Build Docker Images từ Source

### 1. Build AAS Web UI

```powershell
cd basyx-aas-web-ui/aas-web-ui
docker build -t basyx-aas-web-ui:local .
cd ../..
```

### 2. Build AAS Registry (MongoDB)

```powershell
cd basyx-java-server-sdk
# Build toàn bộ project trước
./mvnw clean install -DskipTests

# Build AAS Registry với MongoDB
cd basyx.aasregistry/basyx.aasregistry-service-release-log-mongodb
../../mvnw spring-boot:build-image -DskipTests
cd ../../..
```

**Hoặc dùng Dockerfile:**
```powershell
cd basyx-java-server-sdk/basyx.aasregistry/basyx.aasregistry-service-release-log-mongodb/src/main/docker
docker build -t basyx-aas-registry:local .
cd ../../../../../..
```

### 3. Build AAS Repository (Server)

```powershell
cd basyx-java-server-sdk/basyx.aasrepository/basyx.aasrepository.component
docker build -t basyx-aas-repository:local .
cd ../../..
```

### 4. Build AAS Environment (All-in-one)

```powershell
cd basyx-java-server-sdk/basyx.aasenvironment/basyx.aasenvironment.component
docker build -t basyx-aas-environment:local .
cd ../../..
```

## 📝 Cập nhật docker-compose.yml

### Option 1: Sử dụng images đã build (Khuyến nghị)

Thay đổi trong `docker-compose.yml`:

```yaml
services:
  # AAS Registry - Sử dụng image local
  aas-registry:
    image: basyx-aas-registry:local  # ← Đổi từ eclipsebasyx/aas-registry:1.4.0
    container_name: aas-registry
    ports:
      - "4000:4000"
    environment:
      - BASYX_REGISTRY_PATH=registry
      - BASYX_BACKEND=MongoDB
      - BASYX_MONGODB_DBNAME=DigitalTwinDB
      - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB
      - BASYX_CORS=*

  # AAS Server/Repository - Sử dụng image local
  aas-server:
    image: basyx-aas-repository:local  # ← Đổi từ eclipsebasyx/aas-server:1.4.0
    container_name: aas-server
    ports:
      - "4001:4001"
    environment:
      - BASYX_SERVER_PATH=aas-server
      - BASYX_BACKEND=MongoDB
      - BASYX_MONGODB_DBNAME=DigitalTwinDB
      - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB
      - BASYX_CORS=*
    depends_on:
      - aas-registry

  # Web UI - Sử dụng image local
  aas-gui:
    image: basyx-aas-web-ui:local  # ← Đổi từ eclipsebasyx/aas-gui:v230703
    container_name: aas-gui
    ports:
      - "3000:3000"
    volumes:
      - ./aas-gui-config.json:/app/public/config.json:ro
    environment:
      - CHOKIDAR_USEPOLLING=true
      - VITE_REGISTRY_PATH=http://localhost:8888/registry
      - VITE_AAS_SERVER_PATH=http://localhost:8888/aasServer
      - VITE_PRIMARY_COLOR=#00A651
    depends_on:
      - aas-server
```

### Option 2: Build trực tiếp trong docker-compose

Tạo file `docker-compose.local.yml`:

```yaml
services:
  nginx-proxy:
    image: nginx:alpine
    container_name: nginx-proxy
    ports:
      - "8888:8080"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - aas-registry
      - aas-server

  mqtt-broker:
    image: eclipse-mosquitto:1.6
    container_name: mqtt-broker
    ports:
      - "1883:1883"
      - "9001:9001"

  aas-registry:
    build:
      context: ./basyx-java-server-sdk/basyx.aasregistry/basyx.aasregistry-service-release-log-mongodb
      dockerfile: src/main/docker/Dockerfile
    container_name: aas-registry
    ports:
      - "4000:4000"
    environment:
      - BASYX_REGISTRY_PATH=registry
      - BASYX_BACKEND=MongoDB
      - BASYX_MONGODB_DBNAME=DigitalTwinDB
      - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB
      - BASYX_CORS=*

  aas-server:
    build:
      context: ./basyx-java-server-sdk/basyx.aasrepository/basyx.aasrepository.component
      dockerfile: Dockerfile
    container_name: aas-server
    ports:
      - "4001:4001"
    environment:
      - BASYX_SERVER_PATH=aas-server
      - BASYX_BACKEND=MongoDB
      - BASYX_MONGODB_DBNAME=DigitalTwinDB
      - BASYX_MONGODB_CONNECTIONURL=mongodb+srv://sa:Admin@123@cluster0.abc.mongodb.net/DigitalTwinDB
      - BASYX_CORS=*
    depends_on:
      - aas-registry

  aas-gui:
    build:
      context: ./basyx-aas-web-ui/aas-web-ui
      dockerfile: Dockerfile
    container_name: aas-gui
    ports:
      - "3000:3000"
    volumes:
      - ./aas-gui-config.json:/app/public/config.json:ro
    environment:
      - CHOKIDAR_USEPOLLING=true
      - VITE_REGISTRY_PATH=http://localhost:8888/registry
      - VITE_AAS_SERVER_PATH=http://localhost:8888/aasServer
      - VITE_PRIMARY_COLOR=#00A651
    depends_on:
      - aas-server
```

Chạy với:
```powershell
docker-compose -f docker-compose.local.yml up --build -d
```

## ⚙️ Yêu cầu Build

### 1. Java (cho basyx-java-server-sdk)
```powershell
# Cần Java 17+
java -version
```

Nếu chưa có, tải: https://adoptium.net/

### 2. Maven (cho Java builds)
```powershell
# Cần Maven 3.8+
mvn -version
```

### 3. Node.js (cho basyx-aas-web-ui)
```powershell
# Cần Node.js 18+
node -v
npm -v
```

## 🚀 Quy trình Thay thế Hoàn chỉnh

### Bước 1: Backup cấu hình hiện tại
```powershell
cp docker-compose.yml docker-compose.yml.backup
```

### Bước 2: Build tất cả images
```powershell
# Build Web UI
cd basyx-aas-web-ui/aas-web-ui
docker build -t basyx-aas-web-ui:local .
cd ../..

# Build Java components (cần Maven)
cd basyx-java-server-sdk
./mvnw clean install -DskipTests
cd ..

# Build AAS Registry
cd basyx-java-server-sdk/basyx.aasregistry/basyx.aasregistry-service-release-log-mongodb/src/main/docker
docker build -t basyx-aas-registry:local .
cd ../../../../../..

# Build AAS Repository
cd basyx-java-server-sdk/basyx.aasrepository/basyx.aasrepository.component
docker build -t basyx-aas-repository:local .
cd ../../..
```

### Bước 3: Dừng hệ thống cũ
```powershell
python stop_system.py
# Hoặc
docker-compose down
```

### Bước 4: Cập nhật docker-compose.yml
Thay đổi images như hướng dẫn ở trên (Option 1)

### Bước 5: Khởi động với images mới
```powershell
python start_system.py
# Hoặc
docker-compose up -d
```

### Bước 6: Kiểm tra
```powershell
# Kiểm tra containers
docker ps

# Kiểm tra logs
docker logs aas-registry
docker logs aas-server
docker logs aas-gui

# Test hệ thống
python check_system.py
```

## 🎯 Ưu điểm Build từ Source

✅ **Tùy chỉnh**: Có thể sửa code, thêm tính năng
✅ **Version mới nhất**: Dùng code mới nhất từ GitHub
✅ **Debug**: Dễ debug và fix lỗi
✅ **Độc lập**: Không phụ thuộc Docker Hub

## ⚠️ Lưu ý

1. **Build lần đầu lâu**: Java build có thể mất 10-30 phút
2. **Cần nhiều RAM**: Ít nhất 8GB RAM cho build Java
3. **Kiểm tra version**: Đảm bảo Java 17+, Maven 3.8+, Node 18+
4. **MongoDB connection**: Cấu hình MongoDB phải giống hệt cũ
5. **Port conflicts**: Đảm bảo port 4000, 4001, 3000 không bị chiếm

## 🆘 Troubleshooting

### Lỗi: Maven not found
```powershell
# Windows: Tải Maven từ https://maven.apache.org/download.cgi
# Hoặc dùng mvnw wrapper trong project
./mvnw clean install
```

### Lỗi: Java version không đúng
```powershell
# Kiểm tra version
java -version
# Cần Java 17+
```

### Lỗi: Build failed - Out of memory
```powershell
# Tăng memory cho Maven
set MAVEN_OPTS=-Xmx2048m
./mvnw clean install -DskipTests
```

### Lỗi: Docker build failed
```powershell
# Xóa cache và build lại
docker builder prune
docker build --no-cache -t basyx-aas-web-ui:local .
```

## 📊 So sánh

| Tiêu chí | Docker Hub Images | Build từ Source |
|----------|-------------------|-----------------|
| Tốc độ setup | ⚡ Nhanh (5 phút) | 🐢 Chậm (30-60 phút) |
| Ổn định | ✅ Rất ổn định | ⚠️ Phụ thuộc build |
| Tùy chỉnh | ❌ Không | ✅ Hoàn toàn |
| Cập nhật | ⚠️ Chậm hơn | ✅ Mới nhất |
| Yêu cầu | 🟢 Chỉ Docker | 🔴 Docker + Java + Maven |

## 💡 Khuyến nghị

- **Môi trường production**: Dùng Docker Hub images
- **Môi trường development**: Build từ source để tùy chỉnh
- **Học tập/Research**: Build từ source để hiểu rõ cơ chế

---

**Bạn muốn tôi giúp build ngay không?** Tôi có thể:
1. Kiểm tra requirements (Java, Maven, Node.js)
2. Build từng component
3. Cập nhật docker-compose.yml
4. Test hệ thống
