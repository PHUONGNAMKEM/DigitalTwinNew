"""
PC Monitor - Giám sát trạng thái máy tính realtime
Thu thập: CPU, RAM, Disk, Network, Temperature
Gửi qua MQTT tới Digital Twin System
"""
import paho.mqtt.client as mqtt
import psutil
import platform
import socket
import time
import json
import os
from datetime import datetime
import sys

# Load .env file nếu có python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==================== CẤU HÌNH ====================
# Đọc từ biến môi trường (.env file)
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Device Configuration - THAY ĐỔI THEO MÁY CỦA BẠN
DEVICE_ID = "PC001"  # ID duy nhất cho máy tính này
DEVICE_NAME = "Workstation-01"
LOCATION = "Workshop Floor 1"

# Topics
TOPIC_TELEMETRY = f"industry/pc/{DEVICE_ID}/telemetry"
TOPIC_STATUS = f"industry/pc/{DEVICE_ID}/status"
TOPIC_HEARTBEAT = f"industry/pc/{DEVICE_ID}/heartbeat"

# Intervals (seconds)
TELEMETRY_INTERVAL = 5  # Gửi telemetry mỗi 5 giây
HEARTBEAT_INTERVAL = 30  # Gửi heartbeat mỗi 30 giây

# ==================== MQTT CLIENT ====================
mqtt_client = mqtt.Client(client_id=f"pc_monitor_{DEVICE_ID}")

# Last Will Testament - Tự động gửi offline khi mất kết nối
mqtt_client.will_set(
    TOPIC_STATUS, 
    json.dumps({
        "device_id": DEVICE_ID,
        "status": "offline",
        "timestamp": datetime.now().isoformat(),
        "reason": "connection_lost"
    }), 
    qos=1, 
    retain=True
)

def on_connect(client, userdata, flags, rc):
    """Callback khi kết nối MQTT thành công"""
    if rc == 0:
        print(f"✓ Đã kết nối MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        
        # Gửi status ONLINE ngay khi kết nối
        status_msg = {
            "device_id": DEVICE_ID,
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "device_info": get_device_info()
        }
        client.publish(TOPIC_STATUS, json.dumps(status_msg), qos=1, retain=True)
        print(f"✓ Đã gửi status: ONLINE")
    else:
        print(f"✗ Kết nối MQTT thất bại, mã lỗi: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback khi mất kết nối MQTT"""
    if rc != 0:
        print(f"⚠ Mất kết nối MQTT. Đang thử kết nối lại...")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

# ==================== THU THẬP DỮ LIỆU ====================

def get_device_info():
    """Lấy thông tin cơ bản về thiết bị"""
    try:
        return {
            "device_id": DEVICE_ID,
            "device_name": DEVICE_NAME,
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "processor": platform.processor(),
            "architecture": platform.machine(),
            "location": LOCATION
        }
    except Exception as e:
        print(f"✗ Lỗi lấy device info: {e}")
        return {}

def get_cpu_info():
    """Lấy thông tin CPU"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        
        # Lấy nhiệt độ CPU (nếu có)
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                cpu_temp = temps['coretemp'][0].current
            elif 'cpu_thermal' in temps:
                cpu_temp = temps['cpu_thermal'][0].current
        except:
            pass
        
        return {
            "cpu_usage": round(cpu_percent, 2),
            "cpu_count": cpu_count,
            "cpu_frequency_current": round(cpu_freq.current, 2) if cpu_freq else None,
            "cpu_frequency_max": round(cpu_freq.max, 2) if cpu_freq else None,
            "cpu_temperature": round(cpu_temp, 2) if cpu_temp else None
        }
    except Exception as e:
        print(f"✗ Lỗi lấy CPU info: {e}")
        return {}

def get_memory_info():
    """Lấy thông tin RAM"""
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "ram_total_mb": round(memory.total / (1024**2), 2),
            "ram_used_mb": round(memory.used / (1024**2), 2),
            "ram_available_mb": round(memory.available / (1024**2), 2),
            "ram_usage_percent": round(memory.percent, 2),
            "swap_total_mb": round(swap.total / (1024**2), 2),
            "swap_used_mb": round(swap.used / (1024**2), 2),
            "swap_usage_percent": round(swap.percent, 2)
        }
    except Exception as e:
        print(f"✗ Lỗi lấy memory info: {e}")
        return {}

def get_disk_info():
    """Lấy thông tin Disk"""
    try:
        disk = psutil.disk_usage('/')
        io_counters = psutil.disk_io_counters()
        
        return {
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_usage_percent": round(disk.percent, 2),
            "disk_read_mb": round(io_counters.read_bytes / (1024**2), 2) if io_counters else None,
            "disk_write_mb": round(io_counters.write_bytes / (1024**2), 2) if io_counters else None
        }
    except Exception as e:
        print(f"✗ Lỗi lấy disk info: {e}")
        return {}

def get_network_info():
    """Lấy thông tin Network"""
    try:
        net_io = psutil.net_io_counters()
        
        return {
            "network_bytes_sent": net_io.bytes_sent,
            "network_bytes_recv": net_io.bytes_recv,
            "network_packets_sent": net_io.packets_sent,
            "network_packets_recv": net_io.packets_recv,
            "network_errors_in": net_io.errin,
            "network_errors_out": net_io.errout
        }
    except Exception as e:
        print(f"✗ Lỗi lấy network info: {e}")
        return {}

def get_boot_time():
    """Lấy thời gian boot và uptime"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = int(time.time() - psutil.boot_time())
        
        return {
            "boot_time": boot_time.isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_hours": round(uptime_seconds / 3600, 2)
        }
    except Exception as e:
        print(f"✗ Lỗi lấy boot time: {e}")
        return {}

def collect_telemetry():
    """Thu thập tất cả telemetry data"""
    telemetry = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.now().isoformat(),
        "status": "online"
    }
    
    # Merge tất cả thông tin
    telemetry.update(get_cpu_info())
    telemetry.update(get_memory_info())
    telemetry.update(get_disk_info())
    telemetry.update(get_network_info())
    telemetry.update(get_boot_time())
    
    return telemetry

# ==================== CHƯƠNG TRÌNH CHÍNH ====================

def send_telemetry():
    """Thu thập và gửi telemetry data"""
    try:
        telemetry = collect_telemetry()
        
        # Gửi qua MQTT
        result = mqtt_client.publish(TOPIC_TELEMETRY, json.dumps(telemetry), qos=0)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            # Hiển thị thông tin quan trọng
            print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Telemetry:")
            print(f"   CPU: {telemetry.get('cpu_usage', 0)}% | "
                  f"RAM: {telemetry.get('ram_usage_percent', 0)}% | "
                  f"Disk: {telemetry.get('disk_usage_percent', 0)}%")
        else:
            print(f"✗ Lỗi gửi telemetry, error code: {result.rc}")
            
    except Exception as e:
        print(f"✗ Lỗi trong send_telemetry: {e}")

def send_heartbeat():
    """Gửi heartbeat để xác nhận máy vẫn hoạt động"""
    try:
        heartbeat = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.now().isoformat(),
            "status": "alive"
        }
        
        mqtt_client.publish(TOPIC_HEARTBEAT, json.dumps(heartbeat), qos=1)
        print(f"💓 [{datetime.now().strftime('%H:%M:%S')}] Heartbeat sent")
        
    except Exception as e:
        print(f"✗ Lỗi gửi heartbeat: {e}")

def main():
    """Main loop"""
    print("\n" + "="*60)
    print(f"🖥️  PC MONITOR - {DEVICE_ID}")
    print("="*60)
    print(f"Device: {DEVICE_NAME}")
    print(f"Location: {LOCATION}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print("="*60)
    
    # Kết nối MQTT
    try:
        print("\n⏳ Đang kết nối MQTT Broker...")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"✗ Không thể kết nối MQTT Broker: {e}")
        sys.exit(1)
    
    # Đợi kết nối
    time.sleep(2)
    
    print("\n✅ Bắt đầu giám sát... (Nhấn Ctrl+C để dừng)\n")
    
    last_telemetry = time.time()
    last_heartbeat = time.time()
    
    try:
        while True:
            current_time = time.time()
            
            # Gửi telemetry
            if current_time - last_telemetry >= TELEMETRY_INTERVAL:
                send_telemetry()
                last_telemetry = current_time
            
            # Gửi heartbeat
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_heartbeat()
                last_heartbeat = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Đang dừng PC Monitor...")
        
        # Gửi status OFFLINE trước khi thoát
        offline_msg = {
            "device_id": DEVICE_ID,
            "status": "offline",
            "timestamp": datetime.now().isoformat(),
            "reason": "manual_shutdown"
        }
        mqtt_client.publish(TOPIC_STATUS, json.dumps(offline_msg), qos=1, retain=True)
        
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("✓ Đã dừng PC Monitor\n")
        
    except Exception as e:
        print(f"\n✗ Lỗi không mong muốn: {e}")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
