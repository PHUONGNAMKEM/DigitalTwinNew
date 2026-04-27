# Hướng dẫn Chạy Dự Án Digital Twin (Local Windows)

Chào bạn, dựa trên trạng thái hiện tại (Docker Desktop đã được bật và các container cốt lõi đã chạy), dự án của bạn gần như đã sẵn sàng hoạt động hoàn toàn. Dưới đây là các bước quy trình chi tiết để bạn tự chạy lên một cách dễ dàng và hoàn chỉnh dự án này!

## Bước 1: Khởi động các Docker Container (Đã hoàn thành)
Bạn đã chạy thành công `docker-compose.yml`, trên phần mềm Docker Desktop của bạn đang có sẵn các container:
- `basyx-environment` (Lưu trữ và API cho chuẩn AAS, cổng 8081)
- `aas-gui` (Giao diện chuẩn của Eclipse BaSyx, cổng 3000 hoặc 3001)
- `mqtt-broker` (Trạm trung chuyển dữ liệu MQTT, cổng 1883)
- `nginx-proxy` (Trạm Proxy giải quyết CORS, cổng 8888)

> **Kiểm tra:** Mở trình duyệt và truy cập [http://localhost:3000](http://localhost:3000) (hoặc [http://localhost:3001](http://localhost:3001)) để đảm bảo giao diện Digital Twin (BaSyx UI) tải thành công.

## Bước 2: Chạy Script Giám Sát PC (Đẩy dữ liệu lên Digital Twin)
Dự án của bạn có kịch bản là lấy thông số thực tế của CPU, RAM, Disk trên máy tính và truyền lên Digital Twin.

1. Bạn có thể mở **Terminal** (PowerShell hoặc VS Code) tại thư mục dự án: 
   `c:\Users\Lenovo\Downloads\FileTaiLieuHK8\ThucTapWisdom\DigitalTwinNew-main\DigitalTwinNew-main`
2. Cài đặt các thư viện cần thiết (mình đã thay bạn chạy kiểm tra và đều đã có sẵn):
   ```bash
   pip install -r requirements.txt
   ```
3. Chạy file chạy giám sát thực tế (Monitor):
   ```bash
   python pc_monitor_integrated.py
   ```
   > Khi chạy, script sẽ tự động tạo mới AAS (Asset) mang tên PC của bạn trên BaSyx, và liên tục đẩy (Push) dữ liệu CPU, RAM tới Server 5s/lần. Để màn hình dòng lệnh này mở trong suốt quá trình chạy.

## Bước 3: Xem kết quả trên Trình duyệt Digital Twin
- **Cuối cùng:** Tải lại trang web giao diện người dùng (http://localhost:3000). 
- **Kết quả:** Bản sao số của máy tính bạn (ví dụ `PC001` tuỳ vào code set up) sẽ xuất hiện trên giao diện.
- Bấm vào biểu tượng đó, tìm mục **OperationalData** -> Bạn sẽ thấy các con số CPU%, RAM% nhảy nhót theo thời gian thực tương đồng với Task Manager của máy tính!

---

> **Lưu ý về Giao diện Tùy Chỉnh (Flask Dashboard)**: 
> File `device_manager_web.py` (Ứng dụng Flask hỗ trợ giao diện phân tích tùy chỉnh với biểu đồ hiển thị) hiện đang bị rỗng khối nội dung (0 bytes) bên trong máy tính của bạn. Do đó, nếu bạn cần chạy Dashboard mới này, bạn sẽ cần dán lại đoạn code Flask Dashboard vào file hoặc cho mình biết để mình có thể khởi tạo lại hoặc hỗ trợ bạn chạy ứng dụng web này nhé.
