"""
Generic Device Updater - Cập nhật dữ liệu cho bất kỳ thiết bị nào
- Giả lập dữ liệu operational để thiết bị hiển thị online
- Tự động detect loại thiết bị và cập nhật dữ liệu phù hợp
"""
import requests
import random
import time
from datetime import datetime
import sys

# Configuration
API_URL = "http://localhost:5000/api"
BASYX_URL = "http://localhost:8081"
UPDATE_INTERVAL = 10  # Cập nhật mỗi 10 giây

def get_all_devices():
    """Lấy danh sách tất cả thiết bị"""
    try:
        response = requests.get(f"{API_URL}/devices")
        if response.status_code == 200:
            data = response.json()
            return data.get('devices', [])
        return []
    except:
        return []

def get_device_operational_fields(device_id):
    """Lấy danh sách các fields trong operational data"""
    try:
        response = requests.get(f"{API_URL}/devices/{device_id}")
        if response.status_code == 200:
            data = response.json()
            operational = data.get('operational', {})
            return list(operational.keys())
        return []
    except:
        return []

def generate_operational_data(device_id, fields):
    """Giả lập dữ liệu operational dựa trên fields có sẵn"""
    data = {}
    
    for field in fields:
        field_lower = field.lower()
        
        # CPU Usage
        if 'cpu' in field_lower and 'usage' in field_lower:
            data[field] = round(random.uniform(10, 90), 2)
        
        # Memory/RAM Usage
        elif ('memory' in field_lower or 'ram' in field_lower) and 'usage' in field_lower:
            data[field] = round(random.uniform(20, 85), 2)
        
        # Disk Usage
        elif 'disk' in field_lower and 'usage' in field_lower:
            data[field] = round(random.uniform(40, 80), 2)
        
        # Network
        elif 'network' in field_lower or 'net' in field_lower:
            if 'sent' in field_lower:
                data[field] = round(random.uniform(100, 5000), 2)
            elif 'received' in field_lower or 'recv' in field_lower:
                data[field] = round(random.uniform(200, 8000), 2)
        
        # Temperature
        elif 'temperature' in field_lower or 'temp' in field_lower:
            if 'nozzle' in field_lower:
                data[field] = round(random.uniform(180, 220), 1)
            elif 'bed' in field_lower:
                data[field] = round(random.uniform(50, 80), 1)
            elif 'engine' in field_lower:
                data[field] = round(random.uniform(70, 95), 1)
            else:
                data[field] = round(random.uniform(20, 40), 1)
        
        # Status
        elif field_lower == 'status' or field_lower == 'operationalstatus':
            statuses = ['Running', 'Idle', 'Active', 'Standby']
            data[field] = random.choice(statuses)
        
        elif field_lower == 'printstatus':
            statuses = ['Idle', 'Printing', 'Paused']
            data[field] = random.choice(statuses)
        
        elif field_lower == 'enginestatus':
            statuses = ['Off', 'Idle', 'Running']
            data[field] = random.choice(statuses)
        
        # Fuel Level
        elif 'fuel' in field_lower and 'level' in field_lower:
            data[field] = round(random.uniform(20, 95), 1)
        
        # Battery Level
        elif 'battery' in field_lower and 'level' in field_lower:
            data[field] = round(random.uniform(30, 100), 1)
        
        # Signal Strength
        elif 'signal' in field_lower and 'strength' in field_lower:
            data[field] = round(random.uniform(-90, -40), 1)
        
        # Progress (Print Progress, etc)
        elif 'progress' in field_lower:
            data[field] = round(random.uniform(0, 100), 1)
        
        # Sensor Value
        elif 'sensor' in field_lower and 'value' in field_lower:
            data[field] = round(random.uniform(20, 30), 2)
        
        # Total Scans / Total Print Time / Engine Hours
        elif 'total' in field_lower or 'engine' in field_lower and 'hour' in field_lower:
            # Incrementing counters - get current and add a bit
            current = random.randint(1000, 5000)
            data[field] = str(current)
        
        # Material Remaining
        elif 'material' in field_lower and 'remaining' in field_lower:
            data[field] = round(random.uniform(100, 1000), 1)
        
        # Error Count
        elif 'error' in field_lower and 'count' in field_lower:
            data[field] = str(random.randint(0, 5))
        
        # Error Code
        elif 'error' in field_lower and 'code' in field_lower:
            codes = ['NONE', 'OK', 'E001', 'W002']
            data[field] = random.choice(codes)
        
        # GPS Location
        elif 'gps' in field_lower or 'location' in field_lower:
            lat = round(random.uniform(10.0, 11.0), 6)
            lon = round(random.uniform(106.0, 107.0), 6)
            data[field] = f"{lat},{lon}"
        
        # Current Job
        elif 'current' in field_lower and 'job' in field_lower:
            data[field] = ""  # Empty when idle
        
        # Timestamp - Always update
        elif 'timestamp' in field_lower or field_lower == 'lastupdate':
            data[field] = datetime.utcnow().isoformat() + "Z"
        
        # Default for unknown fields - small random number
        else:
            data[field] = round(random.uniform(0, 100), 2)
    
    # Always ensure Timestamp exists
    if 'Timestamp' not in data and 'timestamp' not in data and 'LastUpdate' not in data:
        data['Timestamp'] = datetime.utcnow().isoformat() + "Z"
    
    return data

def update_device(device_id, device_name):
    """Cập nhật dữ liệu cho một thiết bị"""
    try:
        # Lấy danh sách fields
        fields = get_device_operational_fields(device_id)
        
        if not fields:
            print(f"[{device_id}] ⚠️  No operational fields found")
            return False
        
        # Generate data
        data = generate_operational_data(device_id, fields)
        
        # Update via API
        response = requests.put(
            f"{API_URL}/devices/{device_id}/operational",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            updated = len(result.get('updated', []))
            total = len(data)
            print(f"[{device_id}] ✓ Updated {updated}/{total} fields - {device_name}")
            return True
        else:
            print(f"[{device_id}] ✗ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[{device_id}] ✗ Error: {e}")
        return False

def monitor_and_update_all_devices():
    """Liên tục cập nhật tất cả thiết bị"""
    print("\n" + "="*70)
    print("🤖 GENERIC DEVICE UPDATER")
    print("="*70)
    print(f"API URL: {API_URL}")
    print(f"Update Interval: {UPDATE_INTERVAL} seconds")
    print("="*70)
    
    # Kiểm tra kết nối
    try:
        response = requests.get(f"{API_URL}/devices")
        if response.status_code != 200:
            print("❌ Cannot connect to Device Manager API")
            sys.exit(1)
        print("✓ Connected to Device Manager API")
    except Exception as e:
        print(f"❌ Cannot connect to Device Manager API: {e}")
        sys.exit(1)
    
    print("\nStarting monitoring loop...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            devices = get_all_devices()
            
            if not devices:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No devices found. Waiting...")
            else:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Updating {len(devices)} device(s):")
                print("-" * 70)
                
                for device in devices:
                    device_id = device.get('id')
                    device_name = device.get('name', 'Unknown')
                    update_device(device_id, device_name)
                
                print("-" * 70)
            
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹  Stopping Generic Device Updater...")
        print("✓ Stopped\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

def update_single_device(device_id):
    """Cập nhật một thiết bị cụ thể (một lần)"""
    print("\n" + "="*70)
    print(f"🎯 UPDATING SINGLE DEVICE: {device_id}")
    print("="*70)
    
    devices = get_all_devices()
    device = next((d for d in devices if d['id'] == device_id), None)
    
    if not device:
        print(f"❌ Device {device_id} not found")
        return False
    
    device_name = device.get('name', 'Unknown')
    success = update_device(device_id, device_name)
    
    if success:
        print(f"\n✓ Successfully updated {device_id}")
        print(f"  Device should now appear as ONLINE in dashboard")
    else:
        print(f"\n✗ Failed to update {device_id}")
    
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generic Device Updater - Giả lập dữ liệu cho thiết bị')
    parser.add_argument('--device', type=str, help='Update a specific device once (e.g., PC-001)')
    parser.add_argument('--interval', type=int, default=10, help='Update interval in seconds (default: 10)')
    
    args = parser.parse_args()
    
    if args.device:
        # Single device update mode
        update_single_device(args.device)
    else:
        # Continuous monitoring mode
        UPDATE_INTERVAL = args.interval
        monitor_and_update_all_devices()
