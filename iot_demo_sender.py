"""
IoT Demo Sender - Giả lập thiết bị IoT gửi dữ liệu qua POST API
Chạy: python iot_demo_sender.py

Script này giả lập một cảm biến IoT gửi dữ liệu nhiệt độ, độ ẩm...
về server mỗi 5 giây qua POST API.
Dùng để demo trước khi có thiết bị IoT thật.
"""
import requests
import time
import random
import math
import json
import sys
from datetime import datetime

# Cấu hình
SERVER_URL = "http://localhost:5000/api/iot/data"
DEVICE_ID = "SENSOR_DEMO_001"
DEVICE_TYPE = "iot_sensor"
SEND_INTERVAL = 5  # Gửi mỗi 5 giây

# Trạng thái cảm biến (thay đổi từ từ, không random hỗn loạn)
class SensorSimulator:
    def __init__(self):
        self.temperature = 25.0  # Nhiệt độ ban đầu
        self.humidity = 60.0     # Độ ẩm ban đầu
        self.battery = 100.0     # Pin ban đầu
        self.signal = -50        # Cường độ tín hiệu (dBm)
        self.tick = 0
    
    def update(self):
        """Cập nhật giá trị theo pattern thực tế"""
        self.tick += 1
        
        # Nhiệt độ: dao động theo sine wave + noise nhỏ
        self.temperature = 25 + 5 * math.sin(self.tick * 0.05) + random.uniform(-0.5, 0.5)
        self.temperature = round(self.temperature, 1)
        
        # Độ ẩm: ngược chiều với nhiệt độ + noise
        self.humidity = 60 - 10 * math.sin(self.tick * 0.05) + random.uniform(-1, 1)
        self.humidity = round(max(30, min(95, self.humidity)), 1)
        
        # Pin: giảm dần rất chậm
        self.battery = max(0, 100 - (self.tick * 0.01))
        self.battery = round(self.battery, 1)
        
        # Tín hiệu: dao động nhẹ
        self.signal = -50 + random.uniform(-5, 5)
        self.signal = round(self.signal, 0)
        
        return {
            "SensorValue": self.temperature,
            "BatteryLevel": self.battery,
            "SignalStrength": self.signal,
            "ErrorCount": 0,
            "Timestamp": datetime.utcnow().isoformat() + "Z"
        }


def main():
    print("\n" + "=" * 60)
    print("📡 IoT DEMO SENDER")
    print("=" * 60)
    print(f"Device ID: {DEVICE_ID}")
    print(f"Server: {SERVER_URL}")
    print(f"Interval: {SEND_INTERVAL}s")
    print("=" * 60)
    
    # Kiểm tra server
    print("\nĐang kiểm tra kết nối server...")
    try:
        response = requests.get("http://localhost:5000/api/devices", timeout=3)
        if response.status_code == 200:
            print("✅ Kết nối server OK!")
        else:
            print(f"⚠️ Server phản hồi: {response.status_code}")
    except Exception as e:
        print(f"❌ Không kết nối được server: {e}")
        print("Hãy chắc chắn device_manager_web.py đang chạy!")
        sys.exit(1)
    
    # Kiểm tra thiết bị đã được tạo chưa
    print(f"\n⚠️ LƯU Ý: Trước khi chạy script này, hãy tạo thiết bị '{DEVICE_ID}'")
    print("   trên giao diện http://localhost:5000 (chọn template IoT Sensor)")
    print("   hoặc thiết bị sẽ nhận dữ liệu nhưng không update được BaSyx.\n")
    
    simulator = SensorSimulator()
    
    print(f"Bắt đầu gửi dữ liệu mỗi {SEND_INTERVAL}s...")
    print("Nhấn Ctrl+C để dừng\n")
    
    try:
        while True:
            # Tạo dữ liệu mới
            sensor_data = simulator.update()
            
            payload = {
                "device_id": DEVICE_ID,
                "device_type": DEVICE_TYPE,
                "source": "demo_simulator",
                "data": sensor_data
            }
            
            # Gửi POST
            try:
                response = requests.post(
                    SERVER_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                result = response.json()
                temp = sensor_data['SensorValue']
                battery = sensor_data['BatteryLevel']
                signal = sensor_data['SignalStrength']
                
                updated_count = len(result.get('updated', []))
                failed_count = len(result.get('failed', []))
                
                status_icon = "✅" if updated_count > 0 else "⚠️"
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_icon} "
                      f"Temp: {temp}°C | Battery: {battery}% | Signal: {signal}dBm | "
                      f"Updated: {updated_count}, Failed: {failed_count}")
                
            except requests.exceptions.Timeout:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ Timeout")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")
            
            time.sleep(SEND_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Đã dừng IoT Demo Sender")


if __name__ == "__main__":
    main()
