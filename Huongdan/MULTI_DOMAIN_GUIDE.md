# Hướng dẫn sử dụng Device Manager - Multi-Domain

## 🌟 Tính năng mới

### 1. **Hỗ trợ nhiều Domain**
Hệ thống không còn bị fix cứng cho máy tính, mà có thể quản lý nhiều loại thiết bị khác nhau:

- 💻 **Computer/Workstation** - Máy tính, máy trạm
- 🏥 **Medical Device** - Thiết bị y tế (MRI, CT, X-quang...)
- 🏗️ **Construction Equipment** - Thiết bị xây dựng (máy xúc, cần cẩu...)
- 🖨️ **3D Printer** - Máy in 3D công nghiệp
- 📡 **IoT Sensor** - Cảm biến IoT
- ⚙️ **Custom Device** - Tự định nghĩa thiết bị

### 2. **Template System**
Mỗi domain có template riêng với:
- **Các trường dữ liệu phù hợp** với domain đó
- **Tooltips hướng dẫn** chi tiết cho từng trường
- **Placeholder và examples** để người dùng biết điền gì
- **Validation** (required/optional)
- **Đúng chuẩn AAS** (Asset Administration Shell)

### 3. **Dynamic Form Generation**
Form tự động sinh ra dựa trên template được chọn, người dùng chỉ cần:
1. Chọn loại thiết bị
2. Điền thông tin theo hướng dẫn
3. Submit

### 4. **Cấu trúc dữ liệu chuẩn AAS**
Mỗi thiết bị có 3 submodels (theo chuẩn Digital Twin):

#### **Nameplate** (Thông tin nhận dạng)
- Thông tin cơ bản: Tên, nhà sản xuất, serial, vị trí
- Không thay đổi trong quá trình vận hành

#### **Technical Data** (Thông số kỹ thuật)
- Thông số kỹ thuật của thiết bị
- Ít thay đổi hoặc không đổi

#### **Operational Data** (Dữ liệu vận hành)
- Dữ liệu thời gian thực
- Cập nhật liên tục (CPU, nhiệt độ, trạng thái...)
- Có **Timestamp** để xác định online/offline

## 📖 Hướng dẫn sử dụng

### Bước 1: Truy cập Dashboard
Mở browser và vào: **http://localhost:5000**

### Bước 2: Thêm thiết bị mới
1. Click nút **"Thêm thiết bị mới"**
2. **Chọn loại thiết bị** (Computer, Medical Device, Construction Equipment...)
3. **Nhập Device ID** (VD: PC001, MED001, CRANE001)
4. **Điền thông tin Nameplate**:
   - Rê chuột vào dấu **"?"** để xem hướng dẫn
   - Các trường có dấu **"*"** là bắt buộc
   - Một số trường có dropdown với gợi ý
5. **Điền thông số kỹ thuật** (Technical Data - tùy chọn)
6. **Thêm trường tùy chỉnh** nếu cần
7. Click **"Tạo thiết bị"**

### Bước 3: Xem thiết bị
- Tự động refresh mỗi 5 giây
- Hiển thị trạng thái online/offline
- Tìm kiếm theo ID, tên, nhà sản xuất, vị trí

## 🎯 Ví dụ cụ thể

### Ví dụ 1: Thêm thiết bị y tế (MRI Scanner)

```
Template: Medical Device 🏥

Device ID: MED-MRI-001

Nameplate:
├─ Nhà sản xuất: Siemens Healthineers
├─ Tên thiết bị: MRI Scanner Magnetom Vida
├─ Số serial: SMHS-MRI-2024-001
├─ Vị trí: Radiology Department - Room 201
└─ Số chứng nhận FDA/CE: FDA-K987654

Technical Data:
├─ Phân loại thiết bị: Class II
├─ Công suất (W): 45000
├─ Điện áp: 480V/60Hz
├─ Kích thước (cm): 250x200x220
└─ Chu kỳ bảo trì (tháng): 6

Operational Data (tự động):
└─ Timestamp: 2026-02-04T14:30:00Z
```

### Ví dụ 2: Thêm thiết bị xây dựng (Máy xúc)

```
Template: Construction Equipment 🏗️

Device ID: CRANE-001

Nameplate:
├─ Nhà sản xuất: Caterpillar
├─ Tên thiết bị: Excavator CAT 320D
├─ Số serial/VIN: CAT0320DXJCB12345
├─ Vị trí/Công trường: Site A - North Zone
└─ Biển số: 29A-12345

Technical Data:
├─ Loại thiết bị: Excavator
├─ Model động cơ: CAT C7.1 ACERT
├─ Công suất động cơ (HP): 158
├─ Trọng lượng vận hành (kg): 20500
└─ Độ sâu đào tối đa (m): 6.5

Operational Data (tự động):
└─ Timestamp: 2026-02-04T14:30:00Z
```

### Ví dụ 3: Thêm máy in 3D

```
Template: 3D Printer 🖨️

Device ID: 3DP-001

Nameplate:
├─ Nhà sản xuất: Ultimaker
├─ Tên thiết bị: Ultimaker S5 Pro Bundle
├─ Số serial: ULT-S5-2024-001
└─ Vị trí: Manufacturing Lab - Station 3

Technical Data:
├─ Công nghệ in: FDM
├─ Khối in (mm): 330x240x300
├─ Độ phân giải lớp (mm): 0.05
├─ Loại vật liệu: PLA, ABS, PETG
└─ Kích thước nozzle (mm): 0.4
```

## 🔧 Tùy chỉnh cho Domain mới

### Cách thêm template cho domain mới:

1. Mở file **`device_templates.json`**
2. Thêm một entry mới trong `"templates"`:

```json
{
  "templates": {
    "your_domain": {
      "name": "Your Domain Name",
      "icon": "🎯",
      "description": "Mô tả ngắn gọn",
      "assetType": "YourDomain/Type",
      "nameplate": [
        {
          "idShort": "ManufacturerName",
          "label": "Nhà sản xuất",
          "valueType": "xs:string",
          "required": true,
          "placeholder": "VD: ABC Company",
          "tooltip": "Tên hãng sản xuất",
          "examples": ["Company A", "Company B"]
        }
        // Thêm các trường khác...
      ],
      "technicalData": [
        // Định nghĩa các trường kỹ thuật
      ],
      "operationalData": [
        {
          "idShort": "Timestamp",
          "label": "Thời gian cập nhật",
          "valueType": "xs:string",
          "category": "PARAMETER",
          "tooltip": "Thời điểm cập nhật dữ liệu"
        }
        // Thêm các trường khác...
      ]
    }
  }
}
```

3. **Restart Flask server**:
```powershell
# Dừng server (Ctrl+C)
# Chạy lại
python device_manager_web.py
```

4. Template mới sẽ xuất hiện trong UI!

## 🎨 Các thuộc tính của Field

```json
{
  "idShort": "FieldName",          // Tên property trong AAS (không dấu, PascalCase)
  "label": "Nhãn hiển thị",       // Tên hiển thị trên UI
  "valueType": "xs:string",        // Kiểu dữ liệu: xs:string, xs:integer, xs:double, xs:boolean
  "required": true,                // Bắt buộc phải điền
  "placeholder": "VD: ...",        // Gợi ý cho người dùng
  "tooltip": "Hướng dẫn chi tiết", // Hiện khi rê chuột vào dấu "?"
  "category": "VARIABLE",          // VARIABLE | PARAMETER (cho operational data)
  "examples": ["A", "B", "C"]      // Danh sách gợi ý (tạo dropdown)
}
```

### Các valueType phổ biến:
- `xs:string` - Chuỗi văn bản
- `xs:integer` - Số nguyên
- `xs:double` - Số thực (decimal)
- `xs:boolean` - True/False
- `xs:dateTime` - Ngày giờ (ISO 8601)

## 📊 Cấu trúc dữ liệu trong BaSyx

### AAS (Asset Administration Shell)
```json
{
  "id": "https://example.com/ids/aas/DEVICE001",
  "idShort": "DEVICE001_AAS",
  "assetInformation": {
    "assetKind": "Instance",
    "globalAssetId": "https://example.com/ids/asset/DEVICE001",
    "assetType": "Medical/Equipment"
  }
}
```

### Submodel - Nameplate
```json
{
  "id": "https://example.com/ids/sm/DEVICE001_Nameplate",
  "idShort": "DEVICE001_Nameplate",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{
      "type": "GlobalReference",
      "value": "https://admin-shell.io/zvei/nameplate/1/0/Nameplate"
    }]
  },
  "submodelElements": [
    {
      "idShort": "ManufacturerName",
      "modelType": "Property",
      "valueType": "xs:string",
      "value": "Siemens",
      "description": [{"language": "en", "text": "Manufacturer name"}]
    }
  ]
}
```

## 🚀 Best Practices

### 1. **Đặt tên Device ID**
- Sử dụng prefix theo domain: `PC-`, `MED-`, `CRANE-`, `3DP-`, `IOT-`
- Thêm số thứ tự: `PC-001`, `PC-002`
- Không dùng ký tự đặc biệt (chỉ A-Z, 0-9, gạch ngang)

### 2. **Chọn valueType đúng**
- Số đếm → `xs:integer`
- Đo lường (có decimal) → `xs:double`
- Văn bản → `xs:string`
- Ngày giờ → `xs:string` (dùng ISO 8601)

### 3. **Operational Data phải có Timestamp**
- Bắt buộc phải có field `Timestamp` trong operational data
- Dùng để xác định thiết bị online/offline
- Format: ISO 8601 (VD: `2026-02-04T14:30:00Z`)

### 4. **Tooltip nên rõ ràng**
- Giải thích field này dùng để làm gì
- Đưa ra ví dụ cụ thể
- Nêu đơn vị đo (nếu có)

### 5. **Sử dụng examples**
- Giúp người dùng chọn nhanh
- Giảm lỗi nhập liệu
- Chuẩn hóa dữ liệu

## 🔍 Xem dữ liệu chi tiết

### Trong BaSyx Web UI
1. Truy cập: http://localhost:3000
2. Chọn AAS từ danh sách
3. Xem các Submodels và Properties

### Qua Swagger API
1. Truy cập: http://localhost:8081/swagger-ui/index.html
2. Test các API endpoints
3. Xem cấu trúc JSON

### Qua Device Manager
1. Dashboard hiển thị tổng quan
2. Card thiết bị hiển thị thông tin cơ bản
3. Click "Chi tiết" để xem trong BaSyx Web UI

## 🆘 Troubleshooting

### Template không hiển thị
- Kiểm tra file `device_templates.json` có đúng format JSON không
- Restart Flask server
- Xem browser console (F12) để check lỗi

### Không tạo được thiết bị
- Kiểm tra BaSyx server đang chạy: `docker-compose ps`
- Xem log Flask server
- Kiểm tra Device ID đã tồn tại chưa

### Thiết bị hiển thị offline
- Kiểm tra Operational Data có field `Timestamp` không
- Timestamp phải được cập nhật trong vòng 60 giây
- Sử dụng script giả lập hoặc pc_monitor để cập nhật dữ liệu

## 📝 Tổng kết

Hệ thống mới có những ưu điểm:

✅ **Linh hoạt** - Dễ dàng thêm domain mới  
✅ **Chuẩn hóa** - Tuân thủ chuẩn AAS  
✅ **Dễ sử dụng** - Có tooltips hướng dẫn chi tiết  
✅ **Mở rộng** - Có thể thêm custom fields  
✅ **Đa dạng** - Hỗ trợ nhiều loại thiết bị khác nhau  

Bây giờ bạn có thể quản lý bất kỳ loại thiết bị nào trong Digital Twin ecosystem! 🎉
