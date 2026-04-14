"""
Export AAS Model từ MongoDB ra file JSON (AASX-compatible format)
Có thể import vào AASX Package Explorer
"""
from pymongo import MongoClient
import json
from datetime import datetime

# MongoDB Connection
MONGODB_URI = "mongodb+srv://sa:Admin%40123@cluster0.wtpp0cf.mongodb.net/DigitalTwinDB?retryWrites=true&w=majority"
DB_NAME = "DigitalTwinDB"

def export_aas_to_json(device_id="PC001", output_file=None):
    """Export AAS Model ra file JSON"""
    try:
        if output_file is None:
            output_file = f"aas_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print("\n" + "="*70)
        print(f"EXPORT AAS MODEL - {device_id}")
        print("="*70)
        
        # Kết nối MongoDB
        print("\n📡 Đang kết nối MongoDB Atlas...")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[DB_NAME]
        aas_collection = db["aas_models"]
        print("✅ Đã kết nối MongoDB")
        
        # Query AAS Model
        print(f"\n🔍 Đang tìm AAS Model cho {device_id}...")
        aas_model = aas_collection.find_one({"device_id": device_id})
        
        if not aas_model:
            print(f"❌ KHÔNG tìm thấy AAS Model cho {device_id}")
            return
        
        # Remove MongoDB _id field
        if '_id' in aas_model:
            del aas_model['_id']
        
        # Convert datetime to ISO string
        if 'last_update' in aas_model:
            if isinstance(aas_model['last_update'], datetime):
                aas_model['last_update'] = aas_model['last_update'].isoformat()
        
        # Format theo chuẩn AAS JSON Serialization
        aas_export = {
            "assetAdministrationShells": [
                {
                    "modelType": "AssetAdministrationShell",
                    "identification": aas_model.get('identification'),
                    "idShort": aas_model.get('idShort'),
                    "description": aas_model.get('description', []),
                    "administration": aas_model.get('administration'),
                    "asset": aas_model.get('asset'),
                    "submodels": [
                        {
                            "type": "ModelReference",
                            "keys": [
                                {
                                    "type": "Submodel",
                                    "idType": sm.get('identification', {}).get('idType', 'IRI'),
                                    "value": sm.get('identification', {}).get('id', '')
                                }
                            ]
                        }
                        for sm in aas_model.get('submodels', [])
                    ]
                }
            ],
            "submodels": [],
            "assets": [
                aas_model.get('asset', {})
            ]
        }
        
        # Add full submodels
        for sm in aas_model.get('submodels', []):
            submodel_export = {
                "modelType": "Submodel",
                "identification": sm.get('identification'),
                "idShort": sm.get('idShort'),
                "kind": sm.get('kind', 'Instance'),
                "semanticId": sm.get('semanticId'),
                "description": sm.get('description', []),
                "category": sm.get('category'),
                "administration": sm.get('administration'),
                "submodelElements": []
            }
            
            # Add properties as SubmodelElements
            for prop_name, prop_data in sm.get('properties', {}).items():
                if isinstance(prop_data, dict):
                    prop_export = {
                        "modelType": "Property",
                        "idShort": prop_name,
                        "valueType": prop_data.get('valueType', 'string'),
                        "value": str(prop_data.get('value', '')),
                        "category": prop_data.get('category'),
                        "description": prop_data.get('description', []),
                        "semanticId": prop_data.get('semanticId'),
                        "qualifiers": prop_data.get('qualifiers', [])
                    }
                    
                    # Remove None values
                    prop_export = {k: v for k, v in prop_export.items() if v is not None and v != [] and v != ''}
                    
                    submodel_export['submodelElements'].append(prop_export)
            
            aas_export['submodels'].append(submodel_export)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aas_export, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Đã export thành công!")
        print(f"📄 File: {output_file}")
        print(f"📊 Kích thước: {len(json.dumps(aas_export))} bytes")
        
        # Summary
        print(f"\n📋 Nội dung:")
        print(f"   - 1 AAS Shell: {aas_model.get('idShort')}")
        print(f"   - {len(aas_export['submodels'])} Submodels")
        total_properties = sum(len(sm['submodelElements']) for sm in aas_export['submodels'])
        print(f"   - {total_properties} Properties (tổng)")
        
        print(f"\n💡 Để xem trong AASX Package Explorer:")
        print(f"   1. Tải AASX Package Explorer: https://github.com/admin-shell-io/aasx-package-explorer")
        print(f"   2. File > Import > JSON Import")
        print(f"   3. Chọn file: {output_file}")
        
        print("\n" + "="*70)
        
        client.close()
        return output_file
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    export_aas_to_json("PC001")
