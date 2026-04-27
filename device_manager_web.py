"""
Device Manager Web Application
- Web interface để quản lý và giám sát thiết bị
- Sử dụng API từ BaSyx Java server
- Hiển thị trạng thái on/off của thiết bị
- Hỗ trợ dynamic templates cho nhiều domain khác nhau
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import base64
from datetime import datetime, timedelta
import json
import os
import psutil
import platform
import socket
import time
import threading

app = Flask(__name__)
CORS(app)

# Configuration
BASYX_URL = "http://localhost:8081"
DEVICE_TIMEOUT = 60  # Thiết bị được coi là offline sau 60 giây không cập nhật

# MongoDB Direct Connection (for IoT data logging)
try:
    from pymongo import MongoClient
    from dotenv import load_dotenv
    load_dotenv()
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    DB_NAME = os.getenv("MONGODB_DB_NAME", "DigitalTwinDB")
    if MONGODB_URI:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_db = mongo_client[DB_NAME]
        print("✅ MongoDB Atlas connected for IoT data logging")
    else:
        mongo_client = None
        mongo_db = None
        print("⚠️ MONGODB_URI not set, IoT data logging disabled")
except ImportError:
    mongo_client = None
    mongo_db = None
    print("⚠️ pymongo not installed, IoT data logging disabled")
except Exception as e:
    mongo_client = None
    mongo_db = None
    print(f"⚠️ MongoDB connection failed: {e}")

# Load templates
TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), 'device_templates.json')
with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
    DEVICE_TEMPLATES = json.load(f)

def base64_encode(text):
    """Encode text sang base64 URL-safe"""
    encoded = base64.urlsafe_b64encode(text.encode('utf-8')).decode('utf-8')
    return encoded.rstrip('=')

def base64_decode(encoded_text):
    """Decode base64 URL-safe về text"""
    # Thêm padding nếu cần
    padding = 4 - len(encoded_text) % 4
    if padding != 4:
        encoded_text += '=' * padding
    decoded = base64.urlsafe_b64decode(encoded_text.encode('utf-8')).decode('utf-8')
    return decoded

# ==================== API Endpoints ====================

@app.route('/')
def index():
    """Trang chủ - Advanced Dashboard với multi-domain support"""
    return render_template('dashboard_advanced.html')

@app.route('/simple')
def simple_dashboard():
    """Dashboard đơn giản (legacy)"""
    return render_template('dashboard.html')

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Lấy danh sách templates"""
    return jsonify(DEVICE_TEMPLATES), 200

@app.route('/api/devices', methods=['GET'])
def get_all_devices():
    """Lấy danh sách tất cả thiết bị từ BaSyx server"""
    try:
        # Lấy tất cả AAS từ server
        response = requests.get(f"{BASYX_URL}/shells")
        
        if response.status_code != 200:
            return jsonify({"error": "Cannot connect to BaSyx server"}), 500
        
        aas_list = response.json().get('result', [])
        devices = []
        
        for aas in aas_list:
            device_id = aas.get('idShort', 'Unknown').strip()
            aas_id = aas.get('id', '')
            
            # Lấy thông tin operational data để xác định trạng thái
            operational_sm_id = f"https://example.com/ids/sm/{device_id.replace('_AAS', '')}_OperationalData"
            status = check_device_status(operational_sm_id)
            
            # Lấy thông tin nameplate
            nameplate_info = get_nameplate_info(device_id.replace('_AAS', ''))
            
            device_info = {
                "id": device_id.replace('_AAS', ''),
                "name": nameplate_info.get('DeviceName') or f"Thiết bị {device_id.replace('_AAS', '')}",
                "manufacturer": nameplate_info.get('ManufacturerName', 'Unknown'),
                "location": nameplate_info.get('Location', 'Unknown'),
                "status": status['status'],
                "lastUpdate": status['lastUpdate'],
                "aasId": aas_id
            }
            devices.append(device_info)
        
        return jsonify({"devices": devices, "total": len(devices)}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device_detail(device_id):
    """Lấy thông tin chi tiết của một thiết bị"""
    try:
        aas_id = f"https://example.com/ids/aas/{device_id}"
        aas_id_encoded = base64_encode(aas_id)
        
        # Lấy AAS
        response = requests.get(f"{BASYX_URL}/shells/{aas_id_encoded}")
        if response.status_code != 200:
            return jsonify({"error": "Device not found"}), 404
        
        aas_data = response.json()
        
        # Lấy các submodels
        nameplate = get_nameplate_info(device_id)
        technical = get_technical_info(device_id)
        operational = get_operational_info(device_id)
        
        device_detail = {
            "id": device_id,
            "aas": aas_data,
            "nameplate": nameplate,
            "technical": technical,
            "operational": operational,
            "status": check_device_status(f"https://example.com/ids/sm/{device_id}_OperationalData")
        }
        
        return jsonify(device_detail), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['POST'])
def create_device():
    """Tạo thiết bị mới với dynamic template"""
    try:
        data = request.json
        device_id = data.get('deviceId', '').strip()
        template_name = data.get('template', 'custom')
        asset_type = data.get('assetType', 'Unknown')
        
        # Lấy dữ liệu từ các submodels
        nameplate_data = data.get('nameplate', {})
        technical_data = data.get('technicalData', {})
        operational_data = data.get('operationalData', {})
        
        if not device_id:
            return jsonify({"error": "deviceId is required"}), 400
        
        device_name = nameplate_data.get('DeviceName') or f"Thiết bị {device_id}"
        
        # Tạo AAS
        aas_id = f"https://example.com/ids/aas/{device_id}"
        asset_id = f"https://example.com/ids/asset/{device_id}"
        
        aas_data = {
            "id": aas_id,
            "idShort": f"{device_id}_AAS",
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": asset_id,
                "assetType": asset_type
            },
            "description": [
                {
                    "language": "en",
                    "text": f"Asset Administration Shell for {device_name}"
                }
            ]
        }
        
        response = requests.post(
            f"{BASYX_URL}/shells",
            json=aas_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in [200, 201]:
            return jsonify({"error": f"Failed to create AAS: {response.text}"}), 500
        
        # Tạo các Submodels với dữ liệu động và link vào AAS
        submodels_created = []
        
        if nameplate_data:
            sm_id = f"https://example.com/ids/sm/{device_id}_Nameplate"
            if create_dynamic_submodel(device_id, "Nameplate", nameplate_data, template_name):
                if link_submodel_to_aas(aas_id, sm_id):
                    submodels_created.append("Nameplate")
        
        if technical_data:
            sm_id = f"https://example.com/ids/sm/{device_id}_TechnicalData"
            if create_dynamic_submodel(device_id, "TechnicalData", technical_data, template_name):
                if link_submodel_to_aas(aas_id, sm_id):
                    submodels_created.append("TechnicalData")
        
        if operational_data:
            sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
            if create_dynamic_submodel(device_id, "OperationalData", operational_data, template_name):
                if link_submodel_to_aas(aas_id, sm_id):
                    submodels_created.append("OperationalData")
        else:
            # Tạo operational data mặc định với timestamp
            sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
            default_operational = {"Timestamp": datetime.utcnow().isoformat() + "Z"}
            if create_dynamic_submodel(device_id, "OperationalData", default_operational, template_name):
                if link_submodel_to_aas(aas_id, sm_id):
                    submodels_created.append("OperationalData")
        
        return jsonify({
            "message": "Device created successfully",
            "deviceId": device_id,
            "aasId": aas_id,
            "submodels": submodels_created
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Xóa thiết bị - thử nhiều cách tìm AAS ID trên BaSyx"""
    try:
        # Cách 1: Thử với AAS ID chuẩn
        aas_id = f"https://example.com/ids/aas/{device_id}"
        aas_id_encoded = base64_encode(aas_id)

        print(f"[DELETE] Trying standard AAS ID: {aas_id}")
        response = requests.delete(f"{BASYX_URL}/shells/{aas_id_encoded}")

        # Accept both 200 OK and 204 No Content as successful deletion
        if response.status_code in [200, 204]:
            print(f"[DELETE] ✅ Deleted AAS via standard ID: {device_id}")
            delete_submodels(device_id)
            # Xóa dữ liệu IoT trong MongoDB (nếu có)
            if mongo_db is not None:
                try:
                    mongo_db["iot_data_log"].delete_many({"device_id": device_id})
                    print(f"[DELETE] ✅ Cleaned MongoDB data for {device_id}")
                except Exception as e:
                    print(f"[DELETE] ⚠️ MongoDB cleanup failed: {e}")
            return jsonify({"message": "Device deleted successfully"}), 200

        # Cách 2: Nếu 404, tìm AAS thực tế trên BaSyx bằng idShort
        if response.status_code == 404:
            print(f"[DELETE] Standard ID not found (404), searching by idShort...")
            try:
                shells_response = requests.get(f"{BASYX_URL}/shells")
                if shells_response.status_code == 200:
                    aas_list = shells_response.json().get('result', [])
                    # Tìm AAS có idShort khớp với device_id hoặc device_id_AAS
                    target_aas = None
                    for aas in aas_list:
                        id_short_raw = aas.get('idShort', '')
                        actual_aas_id = aas.get('id', '')
                        # Normalize: loại bỏ _AAS suffix và tất cả whitespace thừa
                        id_short_clean = id_short_raw.replace('_AAS', '').strip()
                        print(f"[DELETE] Comparing: '{id_short_clean}' vs '{device_id}'")
                        if id_short_clean == device_id:
                            target_aas = aas
                            break
                    
                    if target_aas:
                        actual_aas_id = target_aas['id']
                        actual_encoded = base64_encode(actual_aas_id)
                        print(f"[DELETE] Found AAS by idShort: {actual_aas_id}")
                        
                        del_response = requests.delete(f"{BASYX_URL}/shells/{actual_encoded}")
                        if del_response.status_code in [200, 204]:
                            print(f"[DELETE] ✅ Deleted AAS via idShort search: {device_id}")
                            delete_submodels(device_id)
                            # Xóa dữ liệu IoT trong MongoDB
                            if mongo_db is not None:
                                try:
                                    mongo_db["iot_data_log"].delete_many({"device_id": device_id})
                                except Exception:
                                    pass
                            return jsonify({"message": "Device deleted successfully"}), 200
                        else:
                            print(f"[DELETE] ❌ Delete via idShort failed: {del_response.status_code} {del_response.text}")
                            return jsonify({"error": f"Failed to delete device: {del_response.text}"}), del_response.status_code
                    else:
                        print(f"[DELETE] ❌ No AAS found with idShort matching {device_id}")
                        return jsonify({"error": f"Device '{device_id}' not found on BaSyx server"}), 404
            except Exception as e:
                print(f"[DELETE] ❌ Fallback search failed: {e}")
                return jsonify({"error": f"Failed to delete device: {str(e)}"}), 500

        return jsonify({"error": f"Failed to delete device: {response.text}"}), response.status_code

    except Exception as e:
        print(f"[DELETE] ❌ Exception: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>/operational', methods=['PUT', 'PATCH'])
def update_operational_data(device_id):
    """Cập nhật operational data của thiết bị"""
    try:
        data = request.json
        sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
        sm_id_encoded = base64_encode(sm_id)
        
        # Tự động thêm Timestamp nếu không có
        if 'Timestamp' not in data:
            data['Timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        # Cập nhật từng property
        updated = []
        failed = []
        
        for key, value in data.items():
            try:
                # Lấy property hiện tại
                url = f"{BASYX_URL}/submodels/{sm_id_encoded}/submodel-elements/{key}"
                get_response = requests.get(url)
                
                if get_response.status_code == 200:
                    property_data = get_response.json()
                    property_data["value"] = str(value)
                    
                    # PUT lại property
                    put_response = requests.put(
                        url,
                        json=property_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if put_response.status_code in [200, 204]:
                        updated.append(key)
                    else:
                        failed.append(key)
                else:
                    failed.append(key)
            except Exception as e:
                failed.append(key)
        
        return jsonify({
            "message": f"Updated {len(updated)}/{len(data)} properties",
            "updated": updated,
            "failed": failed
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== Helper Functions ====================

def check_device_status(submodel_id):
    """Kiểm tra trạng thái thiết bị dựa trên operational data"""
    try:
        sm_id_encoded = base64_encode(submodel_id)
        response = requests.get(f"{BASYX_URL}/submodels/{sm_id_encoded}")
        
        if response.status_code != 200:
            return {"status": "unknown", "lastUpdate": None}
        
        submodel_data = response.json()
        
        # Tìm property Timestamp
        timestamp = None
        for element in submodel_data.get('submodelElements', []):
            if element.get('idShort') == 'Timestamp':
                timestamp = element.get('value')
                break
        
        if not timestamp:
            return {"status": "unknown", "lastUpdate": None}
        
        # Parse timestamp và kiểm tra
        try:
            last_update = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(last_update.tzinfo)
            diff_seconds = (now - last_update).total_seconds()
            
            if diff_seconds < DEVICE_TIMEOUT:
                status = "online"
            else:
                status = "offline"
            
            return {
                "status": status,
                "lastUpdate": timestamp,
                "secondsSinceUpdate": int(diff_seconds)
            }
        except:
            return {"status": "unknown", "lastUpdate": timestamp}
            
    except Exception as e:
        return {"status": "error", "lastUpdate": None, "error": str(e)}

def get_nameplate_info(device_id):
    """Lấy thông tin nameplate"""
    try:
        sm_id = f"https://example.com/ids/sm/{device_id}_Nameplate"
        sm_id_encoded = base64_encode(sm_id)
        response = requests.get(f"{BASYX_URL}/submodels/{sm_id_encoded}")
        
        if response.status_code != 200:
            return {}
        
        submodel_data = response.json()
        info = {}
        
        for element in submodel_data.get('submodelElements', []):
            id_short = element.get('idShort')
            value = element.get('value')
            if id_short and value:
                info[id_short] = value
        
        return info
    except:
        return {}

def get_technical_info(device_id):
    """Lấy thông tin technical"""
    try:
        sm_id = f"https://example.com/ids/sm/{device_id}_TechnicalData"
        sm_id_encoded = base64_encode(sm_id)
        response = requests.get(f"{BASYX_URL}/submodels/{sm_id_encoded}")
        
        if response.status_code != 200:
            return {}
        
        submodel_data = response.json()
        info = {}
        
        for element in submodel_data.get('submodelElements', []):
            id_short = element.get('idShort')
            value = element.get('value')
            if id_short and value:
                info[id_short] = value
        
        return info
    except:
        return {}

def get_operational_info(device_id):
    """Lấy thông tin operational"""
    try:
        sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
        sm_id_encoded = base64_encode(sm_id)
        response = requests.get(f"{BASYX_URL}/submodels/{sm_id_encoded}")
        
        if response.status_code != 200:
            return {}
        
        submodel_data = response.json()
        info = {}
        
        for element in submodel_data.get('submodelElements', []):
            id_short = element.get('idShort')
            value = element.get('value')
            if id_short and value:
                info[id_short] = value
        
        return info
    except:
        return {}

def link_submodel_to_aas(aas_id, sm_id):
    """Gắn Submodel vào AAS (tham khảo từ pc_monitor_integrated.py)"""
    try:
        aas_id_encoded = base64_encode(aas_id)
        
        submodel_ref = {
            "type": "ExternalReference",
            "keys": [
                {
                    "type": "Submodel",
                    "value": sm_id
                }
            ]
        }
        
        response = requests.post(
            f"{BASYX_URL}/shells/{aas_id_encoded}/submodel-refs",
            json=submodel_ref,
            headers={"Content-Type": "application/json"}
        )
        
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"Lỗi link Submodel {sm_id} vào AAS: {e}")
        return False

def create_dynamic_submodel(device_id, submodel_type, data_dict, template_name):
    """Tạo Submodel động từ template và data"""
    sm_id = f"https://example.com/ids/sm/{device_id}_{submodel_type}"
    
    # Lấy template definition nếu có
    template_fields = []
    if template_name in DEVICE_TEMPLATES.get('templates', {}):
        template = DEVICE_TEMPLATES['templates'][template_name]
        if submodel_type == "Nameplate":
            template_fields = template.get('nameplate', [])
        elif submodel_type == "TechnicalData":
            template_fields = template.get('technicalData', [])
        elif submodel_type == "OperationalData":
            template_fields = template.get('operationalData', [])
    
    # Tạo submodel elements từ data
    submodel_elements = []
    
    for key, value in data_dict.items():
        # Tìm field definition trong template
        field_def = next((f for f in template_fields if f.get('idShort') == key), None)
        
        if field_def:
            element = {
                "idShort": key,
                "modelType": "Property",
                "valueType": field_def.get('valueType', 'xs:string'),
                "value": str(value)
            }
            
            # Thêm description nếu có tooltip
            if field_def.get('tooltip'):
                element["description"] = [{
                    "language": "en",
                    "text": field_def['tooltip']
                }]
            
            # Thêm category nếu có
            if field_def.get('category'):
                element["category"] = field_def['category']
        else:
            # Không có trong template, tự động detect type
            element = {
                "idShort": key,
                "modelType": "Property",
                "valueType": detect_value_type(value),
                "value": str(value)
            }
        
        submodel_elements.append(element)
        
    # Tạo các trường còn thiếu từ template với giá trị mặc định
    existing_keys = set(data_dict.keys())
    for field in template_fields:
        key = field.get('idShort')
        if key not in existing_keys:
            value_type = field.get('valueType', 'xs:string')
            default_val = "0" if value_type in ['xs:double', 'xs:integer'] else ""
            
            element = {
                "idShort": key,
                "modelType": "Property",
                "valueType": value_type,
                "value": default_val
            }
            if field.get('tooltip'):
                element["description"] = [{
                    "language": "en",
                    "text": field['tooltip']
                }]
            if field.get('category'):
                element["category"] = field['category']
            submodel_elements.append(element)
    
    # Tạo submodel data
    submodel_data = {
        "id": sm_id,
        "idShort": f"{device_id}_{submodel_type}",
        "kind": "Instance",
        "submodelElements": submodel_elements
    }
    
    # Thêm semantic ID cho Nameplate
    if submodel_type == "Nameplate":
        submodel_data["semanticId"] = {
            "type": "ExternalReference",
            "keys": [{
                "type": "GlobalReference",
                "value": "https://admin-shell.io/zvei/nameplate/1/0/Nameplate"
            }]
        }
    
    try:
        response = requests.post(
            f"{BASYX_URL}/submodels",
            json=submodel_data,
            headers={"Content-Type": "application/json"}
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error creating {submodel_type}: {e}")
        return False

def detect_value_type(value):
    """Tự động detect kiểu dữ liệu"""
    if isinstance(value, bool):
        return "xs:boolean"
    elif isinstance(value, int):
        return "xs:integer"
    elif isinstance(value, float):
        return "xs:double"
    else:
        return "xs:string"

def delete_submodels(device_id):
    """Xóa các submodels của device"""
    submodel_ids = [
        f"https://example.com/ids/sm/{device_id}_Nameplate",
        f"https://example.com/ids/sm/{device_id}_TechnicalData",
        f"https://example.com/ids/sm/{device_id}_OperationalData"
    ]
    
    for sm_id in submodel_ids:
        try:
            sm_id_encoded = base64_encode(sm_id)
            requests.delete(f"{BASYX_URL}/submodels/{sm_id_encoded}")
        except:
            pass

# ==================== PC MONITOR APIs ====================

def get_pc_system_info():
    """Thu thập thông tin hệ thống máy tính (static info)"""
    hostname = socket.gethostname()
    cpu_count = psutil.cpu_count()
    memory_total = round(psutil.virtual_memory().total / (1024**3), 2)
    
    # Lấy disk total - Windows dùng 'C:\\' thay vì '/'
    try:
        disk_total = round(psutil.disk_usage('C:\\').total / (1024**3), 2)
    except:
        disk_total = round(psutil.disk_usage('/').total / (1024**3), 2)
    
    return {
        "hostname": hostname,
        "os": f"{platform.system()} {platform.release()}",
        "processor": platform.processor(),
        "cpu_cores": cpu_count,
        "ram_total_gb": memory_total,
        "disk_total_gb": disk_total,
        "architecture": platform.machine(),
        "python_version": platform.python_version()
    }

def get_pc_realtime_stats():
    """Thu thập thông số thời gian thực (dynamic data)"""
    cpu_usage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    
    try:
        disk = psutil.disk_usage('C:\\')
    except:
        disk = psutil.disk_usage('/')
    
    uptime_seconds = int(time.time() - psutil.boot_time())
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    
    return {
        "cpu_usage": round(cpu_usage, 2),
        "ram_used_gb": round(memory.used / (1024**3), 2),
        "ram_total_gb": round(memory.total / (1024**3), 2),
        "ram_usage_percent": round(memory.percent, 2),
        "disk_used_gb": round(disk.used / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "disk_usage_percent": round(disk.percent, 2),
        "uptime_seconds": uptime_seconds,
        "uptime_display": f"{uptime_hours}h {uptime_minutes}m",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.route('/api/pc-monitor/status', methods=['GET'])
def pc_monitor_status():
    """Lấy thông số realtime của máy tính hiện tại"""
    try:
        system_info = get_pc_system_info()
        realtime_stats = get_pc_realtime_stats()
        
        return jsonify({
            "system": system_info,
            "realtime": realtime_stats
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pc-monitor/register', methods=['POST'])
def pc_monitor_register():
    """Tự động tạo AAS cho máy tính cá nhân với thông tin thật"""
    try:
        system_info = get_pc_system_info()
        realtime_stats = get_pc_realtime_stats()
        
        device_id = f"PC_{system_info['hostname']}"
        
        # Kiểm tra xem AAS đã tồn tại chưa
        aas_id = f"https://example.com/ids/aas/{device_id}"
        aas_id_encoded = base64_encode(aas_id)
        check_response = requests.get(f"{BASYX_URL}/shells/{aas_id_encoded}")
        
        if check_response.status_code == 200:
            # AAS đã tồn tại → chỉ cập nhật operational data
            update_pc_operational_data(device_id, realtime_stats)
            return jsonify({
                "message": "PC đã được đăng ký trước đó, đã cập nhật dữ liệu mới",
                "deviceId": device_id,
                "system": system_info,
                "realtime": realtime_stats,
                "alreadyExists": True
            }), 200
        
        # === Tạo AAS mới ===
        asset_id = f"https://example.com/ids/asset/{device_id}"
        device_name = f"{system_info['hostname']} ({system_info['os']})"
        
        aas_data = {
            "id": aas_id,
            "idShort": f"{device_id}_AAS",
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": asset_id,
                "assetType": "Computer/Workstation"
            },
            "description": [
                {"language": "en", "text": f"Digital Twin for PC {system_info['hostname']}"},
                {"language": "vi", "text": f"Bản sao số cho máy tính {system_info['hostname']}"}
            ]
        }
        
        response = requests.post(
            f"{BASYX_URL}/shells",
            json=aas_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in [200, 201]:
            return jsonify({"error": f"Failed to create AAS: {response.text}"}), 500
        
        # === Tạo Nameplate Submodel ===
        processor_name = system_info['processor']
        manufacturer = processor_name.split(',')[0] if ',' in processor_name else "PC Manufacturer"
        
        nameplate_data = {
            "ManufacturerName": manufacturer,
            "DeviceName": device_name,
            "SerialNumber": system_info['hostname'],
            "Location": "Local Workstation",
            "YearOfConstruction": str(datetime.now().year)
        }
        sm_nameplate_id = f"https://example.com/ids/sm/{device_id}_Nameplate"
        if create_dynamic_submodel(device_id, "Nameplate", nameplate_data, "computer"):
            link_submodel_to_aas(aas_id, sm_nameplate_id)
        
        # === Tạo TechnicalData Submodel ===
        technical_data = {
            "ProcessorName": system_info['processor'],
            "ProcessorCount": str(system_info['cpu_cores']),
            "TotalMemoryGB": str(system_info['ram_total_gb']),
            "DiskSize": str(system_info['disk_total_gb']),
            "OSVersion": system_info['os'],
        }
        sm_technical_id = f"https://example.com/ids/sm/{device_id}_TechnicalData"
        if create_dynamic_submodel(device_id, "TechnicalData", technical_data, "computer"):
            link_submodel_to_aas(aas_id, sm_technical_id)
        
        # === Tạo OperationalData Submodel ===
        operational_data = {
            "CPUUsage": str(realtime_stats['cpu_usage']),
            "MemoryUsage": str(realtime_stats['ram_usage_percent']),
            "DiskUsage": str(realtime_stats['disk_usage_percent']),
            "Timestamp": realtime_stats['timestamp']
        }
        sm_operational_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
        if create_dynamic_submodel(device_id, "OperationalData", operational_data, "computer"):
            link_submodel_to_aas(aas_id, sm_operational_id)
        
        return jsonify({
            "message": "PC đã được đăng ký thành công!",
            "deviceId": device_id,
            "aasId": aas_id,
            "system": system_info,
            "realtime": realtime_stats,
            "alreadyExists": False
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_pc_operational_data(device_id, realtime_stats):
    """Cập nhật operational data cho PC đã đăng ký"""
    sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
    sm_id_encoded = base64_encode(sm_id)
    
    updates = {
        "CPUUsage": str(realtime_stats['cpu_usage']),
        "MemoryUsage": str(realtime_stats['ram_usage_percent']),
        "DiskUsage": str(realtime_stats['disk_usage_percent']),
        "Timestamp": realtime_stats['timestamp']
    }
    
    for key, value in updates.items():
        try:
            url = f"{BASYX_URL}/submodels/{sm_id_encoded}/submodel-elements/{key}"
            get_response = requests.get(url)
            if get_response.status_code == 200:
                property_data = get_response.json()
                property_data["value"] = value
                requests.put(url, json=property_data, headers={"Content-Type": "application/json"})
        except:
            pass

@app.route('/api/pc-monitor/update', methods=['POST'])
def pc_monitor_update():
    """Cập nhật thông số mới nhất của PC vào BaSyx"""
    try:
        system_info = get_pc_system_info()
        realtime_stats = get_pc_realtime_stats()
        device_id = f"PC_{system_info['hostname']}"
        
        update_pc_operational_data(device_id, realtime_stats)
        
        return jsonify({
            "message": "Updated",
            "deviceId": device_id,
            "realtime": realtime_stats
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== IOT DATA ENDPOINT ====================

@app.route('/api/iot/data', methods=['POST'])
def receive_iot_data():
    """
    Nhận dữ liệu từ thiết bị IoT.
    Sau này, thiết bị IoT thật chỉ cần POST JSON vào endpoint này.
    
    Body:
    {
        "device_id": "SENSOR-001",
        "device_type": "iot_sensor",
        "data": {
            "SensorValue": 28.5,
            "BatteryLevel": 87.0
        }
    }
    """
    try:
        payload = request.json
        device_id = payload.get('device_id')
        device_type = payload.get('device_type', 'unknown')
        data = payload.get('data', {})
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        if not data:
            return jsonify({"error": "data object is required"}), 400
        
        # Tự động thêm Timestamp nếu không có
        if 'Timestamp' not in data:
            data['Timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        # 1. Cập nhật OperationalData vào BaSyx
        sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
        sm_id_encoded = base64_encode(sm_id)
        
        updated = []
        failed = []
        
        for key, value in data.items():
            try:
                url = f"{BASYX_URL}/submodels/{sm_id_encoded}/submodel-elements/{key}"
                get_response = requests.get(url)
                
                if get_response.status_code == 200:
                    property_data = get_response.json()
                    property_data["value"] = str(value)
                    put_response = requests.put(
                        url,
                        json=property_data,
                        headers={"Content-Type": "application/json"}
                    )
                    if put_response.status_code in [200, 204]:
                        updated.append(key)
                    else:
                        failed.append(key)
                else:
                    failed.append(key)
            except Exception:
                failed.append(key)
        
        # 2. Lưu vào MongoDB (nếu có kết nối) - để có lịch sử
        if mongo_db is not None:
            try:
                iot_log = {
                    "device_id": device_id,
                    "device_type": device_type,
                    "data": data,
                    "source": payload.get('source', 'iot_device'),
                    "received_at": datetime.utcnow(),
                    "updated_properties": updated,
                    "failed_properties": failed
                }
                mongo_db["iot_data_log"].insert_one(iot_log)
            except Exception as e:
                print(f"Warning: MongoDB log failed: {e}")
        
        return jsonify({
            "message": f"Received data for {device_id}",
            "updated": updated,
            "failed": failed,
            "timestamp": data.get('Timestamp')
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/iot/data', methods=['GET'])
def get_iot_data_log():
    """Xem lịch sử dữ liệu IoT đã nhận (cho debug)"""
    try:
        if mongo_db is None:
            return jsonify({"error": "MongoDB not connected", "data": []}), 200
        
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 50))
        
        query = {}
        if device_id:
            query["device_id"] = device_id
        
        logs = list(
            mongo_db["iot_data_log"]
            .find(query, {"_id": 0})
            .sort("received_at", -1)
            .limit(limit)
        )
        
        # Convert datetime objects to string for JSON
        for log in logs:
            if 'received_at' in log:
                log['received_at'] = log['received_at'].isoformat() + "Z"
        
        return jsonify({
            "total": len(logs),
            "data": logs
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== MQTT SUBSCRIBER ====================

class MqttManager:
    """
    Quản lý kết nối MQTT và subscribe topics cho các thiết bị IoT.
    Chạy trên background thread, không block Flask.
    Khi nhận được message → cập nhật BaSyx + lưu MongoDB.
    """
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.broker_host = os.getenv("MQTT_BROKER", "localhost")
        self.broker_port = int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "")
        self.use_tls = os.getenv("MQTT_USE_TLS", "false").lower() in ("true", "1", "yes")
        self.thread = None
        self.running = False
        
        # Load custom config if saved
        self._load_config()
        
        # Cấu hình subscriptions: {device_id: {topic, device_type, field_mapping}}
        self.subscriptions = {}
        
        # Đọc subscriptions đã lưu từ file (nếu có)
        self._load_subscriptions()
        
    def _load_config(self):
        """Đọc cấu hình MQTT từ file (ưu tiên cao hơn biến môi trường)"""
        config_file = os.path.join(os.path.dirname(__file__), 'mqtt_config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.broker_host = config.get('broker_host', self.broker_host)
                    self.broker_port = config.get('broker_port', self.broker_port)
                    self.mqtt_username = config.get('mqtt_username', self.mqtt_username)
                    if 'mqtt_password' in config:
                        self.mqtt_password = config.get('mqtt_password', self.mqtt_password)
                    self.use_tls = config.get('use_tls', self.use_tls)
            except Exception as e:
                print(f"⚠️ Error loading MQTT config: {e}")
                
    def _save_config(self):
        """Lưu cấu hình MQTT ra file"""
        config_file = os.path.join(os.path.dirname(__file__), 'mqtt_config.json')
        try:
            config = {
                "broker_host": self.broker_host,
                "broker_port": self.broker_port,
                "mqtt_username": self.mqtt_username,
                "mqtt_password": self.mqtt_password,
                "use_tls": self.use_tls
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving MQTT config: {e}")
    
    def _load_subscriptions(self):
        """Đọc cấu hình subscriptions từ file"""
        config_file = os.path.join(os.path.dirname(__file__), 'mqtt_subscriptions.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.subscriptions = json.load(f)
                print(f"📡 Loaded {len(self.subscriptions)} MQTT subscriptions from config")
            except Exception as e:
                print(f"⚠️ Error loading MQTT subscriptions: {e}")
    
    def _save_subscriptions(self):
        """Lưu cấu hình subscriptions ra file"""
        config_file = os.path.join(os.path.dirname(__file__), 'mqtt_subscriptions.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.subscriptions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving MQTT subscriptions: {e}")
    
    def start(self):
        """Khởi động MQTT client trên background thread"""
        if self.running:
            return {"status": "already_running"}
        
        try:
            import paho.mqtt.client as mqtt
            import ssl
            
            # Auto-detect transport: port 8884 = websockets, 8883 = tcp
            if self.broker_port == 8884:
                transport = "websockets"
            else:
                transport = "tcp"
            
            # paho-mqtt v2.x sử dụng CallbackAPIVersion
            try:
                from paho.mqtt.enums import CallbackAPIVersion
                self.client = mqtt.Client(
                    callback_api_version=CallbackAPIVersion.VERSION2,
                    client_id="device_manager_web",
                    transport=transport,
                    protocol=mqtt.MQTTv311,
                )
            except ImportError:
                # paho-mqtt v1.x fallback
                self.client = mqtt.Client(
                    client_id="device_manager_web",
                    transport=transport,
                    clean_session=True
                )
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Cấu hình TLS nếu cần (HiveMQ Cloud, AWS IoT, etc.)
            if self.use_tls:
                context = ssl.create_default_context()
                try:
                    import certifi
                    context.load_verify_locations(certifi.where())
                except ImportError:
                    pass  # Use system CA
                self.client.tls_set_context(context)
                print("[MQTT] TLS enabled (ssl.create_default_context)")
            
            # WebSocket path cho HiveMQ Cloud
            if transport == "websockets":
                self.client.ws_set_options(path="/mqtt")
                print(f"[MQTT] WebSocket transport, path=/mqtt")
            
            # Cấu hình username/password nếu có
            if self.mqtt_username:
                self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
                print(f"[MQTT] Auth: {self.mqtt_username}")
            
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            
            tls_label = " (TLS)" if self.use_tls else ""
            return {"status": "started", "broker": f"{self.broker_host}:{self.broker_port}{tls_label}"}
        except Exception as e:
            self.running = False
            return {"status": "error", "message": str(e)}
    
    def stop(self):
        """Dừng MQTT client"""
        self.running = False
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass
        self.connected = False
        return {"status": "stopped"}
    
    def _run(self):
        """Background thread chạy MQTT loop"""
        try:
            print(f"[MQTT] Connecting to {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            self.connected = False
            self.running = False
    
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Callback khi kết nối MQTT (compatible with paho v2)"""
        rc_str = str(reason_code)
        if rc_str == "Success" or reason_code == 0:
            self.connected = True
            print(f"[MQTT] Connected to {self.broker_host}:{self.broker_port}")
            
            # Subscribe lại tất cả topics đã cấu hình
            for device_id, config in self.subscriptions.items():
                topic = config.get('topic')
                if topic:
                    client.subscribe(topic)
                    print(f"   [MQTT] Subscribed: {topic} -> {device_id}")
        else:
            print(f"[MQTT] Connection rejected: {rc_str}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, flags, reason_code=None, properties=None):
        """Callback khi mất kết nối (compatible with paho v2)"""
        self.connected = False
        print(f"[MQTT] Disconnected (reason={reason_code})")
        
        # Tự động reconnect nếu vẫn đang running
        rc_str = str(reason_code) if reason_code else "0"
        if self.running and rc_str != "Success" and reason_code != 0:
            print("   Attempting reconnect in 5s...")
            time.sleep(5)
            try:
                client.reconnect()
            except:
                pass
    
    def _on_message(self, client, userdata, msg):
        """Callback khi nhận message MQTT → cập nhật BaSyx + MongoDB"""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode('utf-8')
            
            # Parse JSON
            try:
                data = json.loads(payload_str)
            except json.JSONDecodeError:
                print(f"⚠️ MQTT: Invalid JSON from {topic}")
                return
            
            # Tìm device_id tương ứng với topic
            device_id = None
            device_config = None
            
            for dev_id, config in self.subscriptions.items():
                if self._topic_matches(config.get('topic', ''), topic):
                    device_id = dev_id
                    device_config = config
                    break
            
            if not device_id:
                # Topic không khớp với device nào → dùng device_id từ payload
                device_id = data.get('device_id', 'unknown')
                device_config = {}
            
            # Áp dụng field mapping nếu có
            field_mapping = device_config.get('field_mapping', {})
            mapped_data = {}
            for key, value in data.items():
                # Nếu có mapping, đổi tên field
                mapped_key = field_mapping.get(key, key)
                mapped_data[mapped_key] = value
            
            # Thêm Timestamp nếu chưa có
            if 'Timestamp' not in mapped_data:
                mapped_data['Timestamp'] = datetime.utcnow().isoformat() + "Z"
            
            # Cập nhật BaSyx OperationalData
            sm_id = f"https://example.com/ids/sm/{device_id}_OperationalData"
            sm_id_encoded = base64_encode(sm_id)
            
            updated = []
            for key, value in mapped_data.items():
                try:
                    url = f"{BASYX_URL}/submodels/{sm_id_encoded}/submodel-elements/{key}"
                    get_response = requests.get(url, timeout=3)
                    if get_response.status_code == 200:
                        property_data = get_response.json()
                        property_data["value"] = str(value)
                        requests.put(url, json=property_data, 
                                   headers={"Content-Type": "application/json"}, timeout=3)
                        updated.append(key)
                except:
                    pass
            
            # Lưu vào MongoDB
            if mongo_db is not None:
                try:
                    mongo_db["iot_data_log"].insert_one({
                        "device_id": device_id,
                        "device_type": device_config.get('device_type', 'mqtt'),
                        "data": mapped_data,
                        "source": "mqtt",
                        "mqtt_topic": topic,
                        "received_at": datetime.utcnow(),
                        "updated_properties": updated
                    })
                except:
                    pass
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 MQTT [{topic}] → {device_id}: "
                  f"updated {len(updated)} properties")
            
        except Exception as e:
            print(f"❌ MQTT message error: {e}")
    
    def _topic_matches(self, pattern, topic):
        """Kiểm tra topic có khớp pattern (hỗ trợ wildcard + và #)"""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        for i, p in enumerate(pattern_parts):
            if p == '#':
                return True  # # matches everything after
            if i >= len(topic_parts):
                return False
            if p == '+':
                continue  # + matches one level
            if p != topic_parts[i]:
                return False
        
        return len(pattern_parts) == len(topic_parts)
    
    def add_subscription(self, device_id, topic, device_type='iot_sensor', field_mapping=None):
        """Thêm subscription mới cho thiết bị"""
        self.subscriptions[device_id] = {
            "topic": topic,
            "device_type": device_type,
            "field_mapping": field_mapping or {},
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        self._save_subscriptions()
        
        # Subscribe ngay nếu đã kết nối
        if self.connected and self.client:
            self.client.subscribe(topic)
            print(f"📡 Subscribed: {topic} → {device_id}")
        
        return self.subscriptions[device_id]
    
    def remove_subscription(self, device_id):
        """Xóa subscription"""
        if device_id in self.subscriptions:
            topic = self.subscriptions[device_id].get('topic')
            del self.subscriptions[device_id]
            self._save_subscriptions()
            
            # Unsubscribe nếu đã kết nối
            if self.connected and self.client and topic:
                self.client.unsubscribe(topic)
            
            return True
        return False
    
    def get_status(self):
        """Lấy trạng thái hiện tại"""
        return {
            "running": self.running,
            "connected": self.connected,
            "broker": f"{self.broker_host}:{self.broker_port}",
            "subscriptions_count": len(self.subscriptions),
            "subscriptions": self.subscriptions
        }

# Khởi tạo MQTT Manager (global)
mqtt_manager = MqttManager()

# ==================== MQTT APIs ====================

@app.route('/api/mqtt/status', methods=['GET'])
def mqtt_status():
    """Lấy trạng thái MQTT"""
    return jsonify(mqtt_manager.get_status()), 200

@app.route('/api/mqtt/config', methods=['GET'])
def get_mqtt_config():
    """Lấy cấu hình MQTT hiện tại"""
    return jsonify({
        "broker_host": mqtt_manager.broker_host,
        "broker_port": mqtt_manager.broker_port,
        "mqtt_username": mqtt_manager.mqtt_username,
        "has_password": bool(mqtt_manager.mqtt_password),
        "use_tls": mqtt_manager.use_tls
    }), 200

@app.route('/api/mqtt/config', methods=['POST'])
def save_mqtt_config():
    """Lưu cấu hình MQTT mới và khởi động lại nếu đang chạy"""
    try:
        data = request.json
        mqtt_manager.broker_host = data.get('broker_host', mqtt_manager.broker_host)
        mqtt_manager.broker_port = int(data.get('broker_port', mqtt_manager.broker_port))
        mqtt_manager.mqtt_username = data.get('mqtt_username', mqtt_manager.mqtt_username)
        if 'mqtt_password' in data and data['mqtt_password'] != '******':
            mqtt_manager.mqtt_password = data['mqtt_password']
        if 'use_tls' in data:
            mqtt_manager.use_tls = data['use_tls']
            
        mqtt_manager._save_config()
        
        was_running = mqtt_manager.running
        if was_running:
            mqtt_manager.stop()
            time.sleep(1) # Đợi cho connection ngắt an toàn
            mqtt_manager.start()
            
        return jsonify({"message": "Cập nhật cấu hình MQTT thành công"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mqtt/start', methods=['POST'])
def mqtt_start():
    """Khởi động MQTT subscriber"""
    result = mqtt_manager.start()
    return jsonify(result), 200

@app.route('/api/mqtt/stop', methods=['POST'])
def mqtt_stop():
    """Dừng MQTT subscriber"""
    result = mqtt_manager.stop()
    return jsonify(result), 200

@app.route('/api/mqtt/subscriptions', methods=['GET'])
def mqtt_get_subscriptions():
    """Lấy danh sách subscriptions"""
    return jsonify(mqtt_manager.subscriptions), 200

@app.route('/api/mqtt/subscriptions', methods=['POST'])
def mqtt_add_subscription():
    """
    Thêm MQTT subscription cho thiết bị.
    Body:
    {
        "device_id": "SENSOR-001",
        "topic": "industry/sensors/SENSOR-001/telemetry",
        "device_type": "iot_sensor",
        "field_mapping": {
            "temperature": "SensorValue",
            "battery": "BatteryLevel"
        }
    }
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        topic = data.get('topic')
        
        if not device_id or not topic:
            return jsonify({"error": "device_id and topic are required"}), 400
        
        result = mqtt_manager.add_subscription(
            device_id=device_id,
            topic=topic,
            device_type=data.get('device_type', 'iot_sensor'),
            field_mapping=data.get('field_mapping', {})
        )
        
        return jsonify({
            "message": f"Subscription added for {device_id}",
            "subscription": result
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mqtt/subscriptions/<device_id>', methods=['DELETE'])
def mqtt_remove_subscription(device_id):
    """Xóa MQTT subscription"""
    if mqtt_manager.remove_subscription(device_id):
        return jsonify({"message": f"Subscription removed for {device_id}"}), 200
    else:
        return jsonify({"error": "Subscription not found"}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("Device Manager Web Application")
    print("=" * 60)
    print(f"BaSyx Server: {BASYX_URL}")
    print(f"Web Server: http://localhost:5000")
    print(f"MQTT Broker: {mqtt_manager.broker_host}:{mqtt_manager.broker_port}")
    print("=" * 60)
    
    # Tự động khởi động MQTT nếu có subscriptions
    if mqtt_manager.subscriptions:
        print(f"\n📡 Auto-starting MQTT with {len(mqtt_manager.subscriptions)} subscriptions...")
        mqtt_manager.start()
    else:
        print("\nℹ️ MQTT chưa có subscription. Cấu hình trên dashboard hoặc gọi API.")
    
    print()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
