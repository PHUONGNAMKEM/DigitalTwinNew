"""
BaSyx Data Bridge - Kết nối MQTT với MongoDB Atlas và AAS Server
Cầu nối dữ liệu từ thiết bị IoT qua MQTT tới Digital Twin

CHỨC NĂNG:
1. Subscribe MQTT topics từ PC monitors
2. Lưu telemetry data vào MongoDB Atlas
3. Theo dõi status online/offline
4. Tạo và cập nhật AAS models trong BaSyx
5. Trigger events khi có thay đổi quan trọng
"""
import paho.mqtt.client as mqtt
import time
import json
import os
from datetime import datetime
from pymongo import MongoClient
import requests
from urllib.parse import quote

# Load .env file nếu có python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==================== CẤU HÌNH ====================
# Đọc từ biến môi trường (.env file)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://sa:Admin%40123@cluster0.wtpp0cf.mongodb.net/DigitalTwinDB?retryWrites=true&w=majority")
DB_NAME = os.getenv("MONGODB_DB_NAME", "DigitalTwinDB")

# MQTT Broker
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")  # hoặc "mqtt-broker" nếu chạy trong Docker
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPICS = [
    "industry/pc/+/telemetry",  # + = wildcard cho device_id
    "industry/pc/+/status",
    "industry/pc/+/heartbeat"
]

# BaSyx AAS Framework - Qua nginx proxy để tránh CORS
AAS_SERVER_URL = "http://localhost:8888/aasServer"
AAS_REGISTRY_URL = "http://localhost:8888/registry"

# Thresholds cho cảnh báo
ALERT_THRESHOLDS = {
    "cpu_usage": 90.0,  # %
    "ram_usage_percent": 85.0,  # %
    "disk_usage_percent": 90.0  # %
}

class DataBridge:
    def __init__(self):
        """Khởi tạo Data Bridge"""
        print("\n" + "="*60)
        print("BaSyx Data Bridge dang khoi dong...")
        print("="*60)
        
        # Kết nối MongoDB Atlas
        try:
            print("Dang ket noi MongoDB Atlas...")
            self.mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            self.mongo_client.server_info()
            self.db = self.mongo_client[DB_NAME]
            
            # Tạo/sử dụng các collections
            self.telemetry_collection = self.db["telemetry_history"]
            self.status_collection = self.db["pc_status"]
            self.aas_collection = self.db["aas_models"]
            self.events_collection = self.db["events"]
            
            # Tạo indexes để tăng tốc query
            self.telemetry_collection.create_index([("device_id", 1), ("timestamp", -1)])
            self.status_collection.create_index("device_id", unique=True)
            
            print("OK - Da ket noi MongoDB Atlas")
            print(f"  Database: {DB_NAME}")
            print(f"  Collections: telemetry_history, pc_status, aas_models, events")
        except Exception as e:
            print(f"LOI - Loi ket noi MongoDB: {e}")
            self.mongo_client = None
        
        # Khởi tạo MQTT Client
        self.mqtt_client = mqtt.Client(client_id="databridge")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Cache để theo dõi status trước đó
        self.previous_status = {}
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback khi kết nối MQTT thành công"""
        if rc == 0:
            print(f"\nOK - Da ket noi MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
            
            # Subscribe tất cả topics
            for topic in MQTT_TOPICS:
                client.subscribe(topic)
                print(f"OK - Da subscribe: {topic}")
        else:
            print(f"LOI - Loi ket noi MQTT, ma loi: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback khi nhận được message từ MQTT"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Parse JSON data
            data = json.loads(payload)
            
            # Xử lý theo loại topic
            if '/telemetry' in topic:
                self.handle_telemetry(topic, data)
            elif '/status' in topic:
                self.handle_status(topic, data)
            elif '/heartbeat' in topic:
                self.handle_heartbeat(topic, data)
            
        except json.JSONDecodeError:
            print(f"LOI - Loi parse JSON tu topic '{topic}'")
        except Exception as e:
            print(f"LOI - Loi xu ly message: {e}")
    
    def handle_telemetry(self, topic, data):
        """Xử lý telemetry data"""
        try:
            device_id = data.get('device_id', 'unknown')
            timestamp = datetime.now()
            
            # Thêm timestamp
            data['timestamp'] = timestamp
            data['topic'] = topic
            
            # Lưu vào MongoDB
            if self.mongo_client:
                self.telemetry_collection.insert_one(data)
            
            # Hiển thị log
            cpu = data.get('cpu_usage', 0)
            ram = data.get('ram_usage_percent', 0)
            disk = data.get('disk_usage_percent', 0)
            
            print(f"\n[{timestamp.strftime('%H:%M:%S')}] Telemetry from {device_id}:")
            print(f"   CPU: {cpu}% | RAM: {ram}% | Disk: {disk}%")
            
            # Kiểm tra thresholds và tạo alerts
            self.check_thresholds(device_id, data)
            
            # Cập nhật AAS Model
            self.update_aas_model(device_id, data)
            
        except Exception as e:
            print(f"LOI - Loi xu ly telemetry: {e}")
    
    def handle_status(self, topic, data):
        """Xử lý status updates (online/offline)"""
        try:
            device_id = data.get('device_id', 'unknown')
            status = data.get('status', 'unknown')
            timestamp = datetime.now()
            
            print(f"\n[{timestamp.strftime('%H:%M:%S')}] Status change: {device_id} -> {status}")
            
            # Lấy status trước đó
            old_status = self.previous_status.get(device_id, None)
            
            # Cập nhật status trong MongoDB
            if self.mongo_client:
                self.status_collection.update_one(
                    {"device_id": device_id},
                    {
                        "$set": {
                            "status": status,
                            "last_seen": timestamp,
                            "device_info": data.get('device_info', {})
                        }
                    },
                    upsert=True
                )
            
            # Nếu status thay đổi, tạo event
            if old_status and old_status != status:
                self.create_event(
                    device_id=device_id,
                    event_type="status_change",
                    event_data={
                        "old_status": old_status,
                        "new_status": status,
                        "reason": data.get('reason', 'unknown')
                    },
                    severity="warning" if status == "offline" else "info"
                )
            
            # Update cache
            self.previous_status[device_id] = status
            
        except Exception as e:
            print(f"LOI - Loi xu ly status: {e}")
    
    def handle_heartbeat(self, topic, data):
        """Xử lý heartbeat messages"""
        device_id = data.get('device_id', 'unknown')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat from {device_id}")
    
    def check_thresholds(self, device_id, data):
        """Kiểm tra các ngưỡng cảnh báo"""
        try:
            alerts = []
            
            # Kiểm tra CPU
            cpu_usage = data.get('cpu_usage', 0)
            if cpu_usage > ALERT_THRESHOLDS['cpu_usage']:
                alerts.append(f"CPU usage cao: {cpu_usage}%")
            
            # Kiểm tra RAM
            ram_usage = data.get('ram_usage_percent', 0)
            if ram_usage > ALERT_THRESHOLDS['ram_usage_percent']:
                alerts.append(f"RAM usage cao: {ram_usage}%")
            
            # Kiểm tra Disk
            disk_usage = data.get('disk_usage_percent', 0)
            if disk_usage > ALERT_THRESHOLDS['disk_usage_percent']:
                alerts.append(f"Disk usage cao: {disk_usage}%")
            
            # Tạo events cho các alerts
            if alerts:
                for alert in alerts:
                    print(f"ALERT: {device_id} - {alert}")
                    self.create_event(
                        device_id=device_id,
                        event_type="threshold_exceeded",
                        event_data={"alert": alert, "metrics": data},
                        severity="warning"
                    )
        except Exception as e:
            print(f"LOI - Loi check thresholds: {e}")
    
    def create_event(self, device_id, event_type, event_data, severity="info"):
        """Tạo event trong MongoDB"""
        try:
            if self.mongo_client:
                event = {
                    "device_id": device_id,
                    "event_type": event_type,
                    "event_data": event_data,
                    "severity": severity,
                    "timestamp": datetime.now(),
                    "acknowledged": False
                }
                self.events_collection.insert_one(event)
        except Exception as e:
            print(f"LOI - Loi tao event: {e}")
    
    def update_aas_model(self, device_id, telemetry_data):
        """Tạo/Cập nhật AAS Model trong MongoDB theo chuẩn Platform Industrie 4.0"""
        try:
            if not self.mongo_client:
                return
            
            # Tạo AAS Model theo chuẩn Asset Administration Shell
            aas_model = {
                "aas_id": f"{device_id}_AAS",
                "device_id": device_id,
                "identification": {
                    "id": f"https://digitaltwin.example.com/aas/{device_id}",
                    "idType": "IRI"
                },
                "idShort": f"{device_id}_WorkstationAAS",
                "description": [
                    {
                        "language": "en",
                        "text": f"Digital Twin for Workstation {device_id}"
                    },
                    {
                        "language": "vi",
                        "text": f"Bản sao số cho Máy trạm {device_id}"
                    }
                ],
                "administration": {
                    "version": "1.0",
                    "revision": "0"
                },
                "asset": {
                    "identification": {
                        "id": f"https://digitaltwin.example.com/asset/{device_id}",
                        "idType": "IRI"
                    },
                    "idShort": f"{device_id}_Asset",
                    "kind": "Instance",
                    "description": [
                        {
                            "language": "en",
                            "text": f"Physical PC Workstation {device_id}"
                        }
                    ]
                },
                "submodels": [
                    {
                        "identification": {
                            "id": f"https://digitaltwin.example.com/{device_id}/TechnicalData",
                            "idType": "IRI"
                        },
                        "idShort": "TechnicalData",
                        "kind": "Instance",
                        "semanticId": {
                            "keys": [
                                {
                                    "type": "GlobalReference",
                                    "idType": "IRI",
                                    "value": "https://admin-shell.io/ZVEI/TechnicalData/Submodel/1/2"
                                }
                            ]
                        },
                        "description": [
                            {
                                "language": "en",
                                "text": "Technical specifications and real-time performance metrics"
                            }
                        ],
                        "category": "VARIABLE",
                        "administration": {
                            "version": "1.0",
                            "revision": "0"
                        },
                        "properties": {
                            "cpu_usage": {
                                "value": telemetry_data.get('cpu_usage', 0),
                                "valueType": "double",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "CPU Usage Percentage"}],
                                "semanticId": {
                                    "keys": [{
                                        "type": "GlobalReference",
                                        "idType": "IRI",
                                        "value": "https://admin-shell.io/idta/CPU_Usage/1/0"
                                    }]
                                },
                                "qualifiers": [
                                    {"type": "Unit", "value": "percent"},
                                    {"type": "MinValue", "value": "0"},
                                    {"type": "MaxValue", "value": "100"}
                                ]
                            },
                            "cpu_temperature": {
                                "value": telemetry_data.get('cpu_temperature'),
                                "valueType": "double",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "CPU Temperature"}],
                                "qualifiers": [
                                    {"type": "Unit", "value": "°C"}
                                ]
                            },
                            "ram_usage_percent": {
                                "value": telemetry_data.get('ram_usage_percent', 0),
                                "valueType": "double",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "RAM Usage Percentage"}],
                                "qualifiers": [
                                    {"type": "Unit", "value": "percent"},
                                    {"type": "MinValue", "value": "0"},
                                    {"type": "MaxValue", "value": "100"}
                                ]
                            },
                            "ram_total_mb": {
                                "value": telemetry_data.get('ram_total_mb', 0),
                                "valueType": "double",
                                "category": "CONSTANT",
                                "description": [{"language": "en", "text": "Total RAM Capacity"}],
                                "qualifiers": [
                                    {"type": "Unit", "value": "MB"}
                                ]
                            },
                            "disk_usage_percent": {
                                "value": telemetry_data.get('disk_usage_percent', 0),
                                "valueType": "double",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "Disk Usage Percentage"}],
                                "qualifiers": [
                                    {"type": "Unit", "value": "percent"},
                                    {"type": "MinValue", "value": "0"},
                                    {"type": "MaxValue", "value": "100"}
                                ]
                            },
                            "disk_total_gb": {
                                "value": telemetry_data.get('disk_total_gb', 0),
                                "valueType": "double",
                                "category": "CONSTANT",
                                "description": [{"language": "en", "text": "Total Disk Capacity"}],
                                "qualifiers": [
                                    {"type": "Unit", "value": "GB"}
                                ]
                            }
                        }
                    },
                    {
                        "identification": {
                            "id": f"https://digitaltwin.example.com/{device_id}/OperationalData",
                            "idType": "IRI"
                        },
                        "idShort": "OperationalData",
                        "kind": "Instance",
                        "semanticId": {
                            "keys": [
                                {
                                    "type": "GlobalReference",
                                    "idType": "IRI",
                                    "value": "https://admin-shell.io/idta/OperationalData/1/0"
                                }
                            ]
                        },
                        "description": [
                            {
                                "language": "en",
                                "text": "Operational status and runtime information"
                            }
                        ],
                        "category": "VARIABLE",
                        "administration": {
                            "version": "1.0",
                            "revision": "0"
                        },
                        "properties": {
                            "status": {
                                "value": telemetry_data.get('status', 'unknown'),
                                "valueType": "string",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "Device Online Status"}]
                            },
                            "uptime_seconds": {
                                "value": telemetry_data.get('uptime_seconds', 0),
                                "valueType": "integer",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "System Uptime"}],
                                "qualifiers": [
                                    {"type": "Unit", "value": "seconds"}
                                ]
                            },
                            "boot_time": {
                                "value": telemetry_data.get('boot_time', ''),
                                "valueType": "string",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "Last Boot Time"}]
                            },
                            "last_update": {
                                "value": datetime.now().isoformat(),
                                "valueType": "string",
                                "category": "VARIABLE",
                                "description": [{"language": "en", "text": "Last Data Update Timestamp"}]
                            }
                        }
                    }
                ],
                "last_update": datetime.now()
            }
            
            # Update hoặc Insert vào MongoDB
            self.aas_collection.update_one(
                {"device_id": device_id},
                {"$set": aas_model},
                upsert=True
            )
            
            # Push lên BaSyx AAS Server
            self.push_to_basyx_server(device_id, aas_model)
            
        except Exception as e:
            print(f"LOI - Loi update AAS model: {e}")
    
    def push_to_basyx_server(self, device_id, aas_model):
        """Push AAS Model lên BaSyx AAS Server qua REST API"""
        try:
            print(f"[DEBUG] Bat dau push AAS cho {device_id}...")
            
            # Format AAS theo chuẩn BaSyx API
            basyx_aas = {
                "modelType": {
                    "name": "AssetAdministrationShell"
                },
                "identification": {
                    "idType": "Custom",
                    "id": f"{device_id}_AAS"
                },
                "idShort": f"{device_id}_WorkstationAAS",
                "asset": {
                    "modelType": {
                        "name": "Asset"
                    },
                    "kind": "Instance",
                    "identification": {
                        "idType": "Custom",
                        "id": f"{device_id}_Asset"
                    },
                    "idShort": f"{device_id}_Asset"
                },
                "submodels": []
            }
            
            # Create/Update AAS Shell tới AAS Server
            aas_id = basyx_aas['identification']['id']
            
            # BaSyx 1.4.0 yêu cầu PUT tới /shells/{id} (không có /aas suffix)
            create_url = f"{AAS_SERVER_URL}/shells/{aas_id}"
            headers = {'Content-Type': 'application/json'}
            
            print(f"[DEBUG] PUT toi: {create_url}")
            response = requests.put(create_url, json=basyx_aas, headers=headers, timeout=5)
            print(f"[DEBUG] Status code: {response.status_code}")
            
            if response.status_code in [200, 201, 204]:  # 204 = No Content (success)
                print(f"  -> Pushed AAS to BaSyx Server: {device_id}")
                
                # Push Submodels với data
                self.push_submodels(device_id, aas_model)
                
                # Register tới AAS Registry
                self.register_to_basyx_registry(device_id, basyx_aas)
            else:
                print(f"[ERROR] Failed to push AAS: {response.status_code}")
                print(f"[DEBUG] Response: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout khi push AAS cho {device_id}")
        except Exception as e:
            print(f"[ERROR] Loi push AAS: {e}")
    
    def push_submodels(self, device_id, aas_model):
        """Push Submodels với properties tới AAS Server theo chuẩn AAS"""
        try:
            for submodel in aas_model.get('submodels', []):
                # Format Submodel theo BaSyx API (simplified version for compatibility)
                basyx_submodel = {
                    "modelType": {
                        "name": "Submodel"
                    },
                    "identification": {
                        "idType": "Custom",
                        "id": f"{device_id}_{submodel['idShort']}"  # Simplified ID
                    },
                    "idShort": submodel['idShort'],
                    "kind": "Instance",
                    "submodelElements": []
                }
                
                # Add Properties với format đơn giản hơn cho BaSyx 1.4.0
                for key, prop_data in submodel.get('properties', {}).items():
                    # Xử lý property có thể là dict (mới) hoặc value đơn giản (cũ)
                    if isinstance(prop_data, dict):
                        value = prop_data.get('value')
                        value_type = prop_data.get('valueType', 'string')
                    else:
                        value = prop_data
                        value_type = 'string'
                    
                    if value is not None:
                        prop = {
                            "modelType": {
                                "name": "Property"
                            },
                            "idShort": key,
                            "valueType": value_type,
                            "value": str(value)
                        }
                        
                        basyx_submodel['submodelElements'].append(prop)
                
                # PUT Submodel - Simplified URL for BaSyx 1.4.0
                sm_id = f"{device_id}_{submodel['idShort']}"
                sm_url = f"{AAS_SERVER_URL}/shells/{device_id}_AAS/aas/submodels/{sm_id}"
                headers = {'Content-Type': 'application/json'}
                response = requests.put(sm_url, json=basyx_submodel, headers=headers, timeout=5)
                
                if response.status_code in [200, 201, 204]:
                    print(f"  -> Pushed Submodel: {submodel['idShort']} ({len(basyx_submodel['submodelElements'])} properties)")
                else:
                    print(f"[ERROR] Submodel {submodel['idShort']} failed: {response.status_code}")
                    print(f"[DEBUG] Response: {response.text[:300]}")
                    
        except Exception as e:
            print(f"[ERROR] Loi push submodels: {e}")
    
    def register_to_basyx_registry(self, device_id, aas_shell):
        """Đăng ký AAS vào BaSyx Registry"""
        try:
            print(f"[DEBUG] Dang dang ky vao Registry cho {device_id}...")
            registry_entry = {
                "modelType": {
                    "name": "AssetAdministrationShellDescriptor"
                },
                "identification": aas_shell['identification'],
                "idShort": aas_shell['idShort'],
                "endpoints": [
                    {
                        "type": "http",
                        "address": f"{AAS_SERVER_URL}/shells/{device_id}_AAS/aas"
                    }
                ],
                "submodels": [
                    {
                        "modelType": {"name": "SubmodelDescriptor"},
                        "identification": {"idType": "Custom", "id": f"{device_id}_TechnicalData"},
                        "idShort": "TechnicalData",
                        "endpoints": [{"type": "http", "address": f"{AAS_SERVER_URL}/shells/{device_id}_AAS/aas/submodels/TechnicalData/submodel"}]
                    },
                    {
                        "modelType": {"name": "SubmodelDescriptor"},
                        "identification": {"idType": "Custom", "id": f"{device_id}_OperationalData"},
                        "idShort": "OperationalData",
                        "endpoints": [{"type": "http", "address": f"{AAS_SERVER_URL}/shells/{device_id}_AAS/aas/submodels/OperationalData/submodel"}]
                    }
                ]
            }
            
            registry_url = f"{AAS_REGISTRY_URL}/api/v1/registry/{device_id}_AAS"
            print(f"[DEBUG] PUT toi Registry: {registry_url}")
            
            headers = {'Content-Type': 'application/json'}
            response = requests.put(registry_url, json=registry_entry, headers=headers, timeout=5)
            print(f"[DEBUG] Registry response: {response.status_code}")
            
            if response.status_code in [200, 201, 409]:
                print(f"  -> Registered to AAS Registry: {device_id}")
            else:
                print(f"[ERROR] Registry failed: {response.status_code}")
                print(f"[DEBUG] Response: {response.text[:300]}")
                
        except Exception as e:
            print(f"[ERROR] Registry exception: {e}")
    
    def start(self):
        """Khởi động Data Bridge"""
        print("\nOK - Data Bridge da san sang!")
        print(f"  - MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"  - MongoDB: {MONGODB_URI[:50]}...")
        print(f"  - Topics: {', '.join(MQTT_TOPICS)}")
        print("\nDang cho du lieu tu MQTT...\n")
        print("="*60 + "\n")
        
        # Kết nối MQTT
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Giữ chương trình chạy
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nDang dung Data Bridge...")
            self.stop()
        except Exception as e:
            print(f"\nLOI - Loi khoi dong: {e}")
            self.stop()
    
    def stop(self):
        """Dừng Data Bridge"""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        if self.mongo_client:
            self.mongo_client.close()
        print("OK - Data Bridge da dung\n")

if __name__ == "__main__":
    bridge = DataBridge()
    bridge.start()
