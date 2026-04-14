"""
Script kiểm tra AAS Model trong MongoDB
Hiển thị đầy đủ metadata theo chuẩn Platform Industrie 4.0
"""
from pymongo import MongoClient
import json
from datetime import datetime

# MongoDB Connection
MONGODB_URI = "mongodb+srv://sa:Admin%40123@cluster0.wtpp0cf.mongodb.net/DigitalTwinDB?retryWrites=true&w=majority"
DB_NAME = "DigitalTwinDB"

def check_aas_model(device_id="PC001"):
    """Kiểm tra AAS Model trong MongoDB"""
    try:
        print("\n" + "="*70)
        print(f"KIỂM TRA AAS MODEL - {device_id}")
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
        
        print("✅ Đã tìm thấy AAS Model\n")
        
        # Kiểm tra các thuộc tính chuẩn
        print("="*70)
        print("1️⃣  ASSET ADMINISTRATION SHELL")
        print("="*70)
        
        checks = []
        
        # Check AAS basic info
        checks.append(("AAS ID", aas_model.get('aas_id'), True))
        checks.append(("idShort", aas_model.get('idShort'), True))
        checks.append(("Identification", aas_model.get('identification'), True))
        checks.append(("Description (đa ngôn ngữ)", aas_model.get('description'), aas_model.get('description') is not None))
        checks.append(("Administration (version/revision)", aas_model.get('administration'), aas_model.get('administration') is not None))
        
        for name, value, has_value in checks:
            status = "✅" if has_value else "❌"
            print(f"{status} {name}: {'Có' if has_value else 'THIẾU'}")
        
        # Check Asset
        print("\n" + "="*70)
        print("2️⃣  ASSET")
        print("="*70)
        
        asset = aas_model.get('asset', {})
        asset_checks = [
            ("Asset Identification", asset.get('identification'), True),
            ("Asset idShort", asset.get('idShort'), True),
            ("Asset Kind", asset.get('kind'), True),
            ("Asset Description", asset.get('description'), asset.get('description') is not None)
        ]
        
        for name, value, has_value in asset_checks:
            status = "✅" if has_value else "❌"
            print(f"{status} {name}: {'Có' if has_value else 'THIẾU'}")
        
        # Check Submodels
        print("\n" + "="*70)
        print("3️⃣  SUBMODELS")
        print("="*70)
        
        submodels = aas_model.get('submodels', [])
        print(f"\n📊 Tổng số Submodels: {len(submodels)}\n")
        
        for idx, sm in enumerate(submodels, 1):
            print(f"\n{'─'*70}")
            print(f"Submodel {idx}: {sm.get('idShort')}")
            print(f"{'─'*70}")
            
            sm_checks = [
                ("Identification", sm.get('identification'), True),
                ("idShort", sm.get('idShort'), True),
                ("Kind", sm.get('kind'), True),
                ("⭐ SemanticId", sm.get('semanticId'), sm.get('semanticId') is not None),
                ("Description", sm.get('description'), sm.get('description') is not None),
                ("Category", sm.get('category'), sm.get('category') is not None),
                ("Administration", sm.get('administration'), sm.get('administration') is not None)
            ]
            
            for name, value, has_value in sm_checks:
                status = "✅" if has_value else "❌"
                if value and name == "⭐ SemanticId":
                    print(f"{status} {name}:")
                    print(f"      {json.dumps(value, indent=6)}")
                else:
                    print(f"{status} {name}: {'Có' if has_value else 'THIẾU'}")
            
            # Check Properties
            properties = sm.get('properties', {})
            print(f"\n   📋 Properties: {len(properties)} items")
            
            for prop_name, prop_data in list(properties.items())[:3]:  # Show first 3
                if isinstance(prop_data, dict):
                    prop_checks = [
                        ("value", prop_data.get('value') is not None),
                        ("valueType", prop_data.get('valueType') is not None),
                        ("category", prop_data.get('category') is not None),
                        ("description", prop_data.get('description') is not None),
                        ("semanticId", prop_data.get('semanticId') is not None),
                        ("qualifiers", prop_data.get('qualifiers') is not None)
                    ]
                    
                    has_all = all([c[1] for c in prop_checks])
                    status = "✅" if has_all else "⚠️"
                    
                    print(f"\n   {status} Property: {prop_name}")
                    for attr_name, has_attr in prop_checks:
                        attr_status = "✅" if has_attr else "❌"
                        print(f"      {attr_status} {attr_name}")
                    
                    # Show qualifiers if exists
                    if prop_data.get('qualifiers'):
                        print(f"      📌 Qualifiers: {prop_data.get('qualifiers')}")
        
        # Summary
        print("\n" + "="*70)
        print("📊 TÓM TẮT")
        print("="*70)
        
        has_descriptions = aas_model.get('description') is not None
        has_admin = aas_model.get('administration') is not None
        has_semantic_ids = all(sm.get('semanticId') for sm in submodels)
        
        # Check if any property has full metadata
        has_full_property_metadata = False
        for sm in submodels:
            for prop_data in sm.get('properties', {}).values():
                if isinstance(prop_data, dict):
                    if (prop_data.get('semanticId') and 
                        prop_data.get('qualifiers') and 
                        prop_data.get('description')):
                        has_full_property_metadata = True
                        break
        
        print(f"\n{'✅' if has_descriptions else '❌'} AAS có description đa ngôn ngữ")
        print(f"{'✅' if has_admin else '❌'} AAS có administration (version/revision)")
        print(f"{'✅' if has_semantic_ids else '❌'} Tất cả Submodels có semanticId")
        print(f"{'✅' if has_full_property_metadata else '❌'} Properties có metadata đầy đủ (semanticId, qualifiers, description)")
        
        if all([has_descriptions, has_admin, has_semantic_ids, has_full_property_metadata]):
            print(f"\n🎉 HOÀN HẢO! AAS Model đã tuân thủ đầy đủ chuẩn Platform Industrie 4.0")
        else:
            print(f"\n⚠️  AAS Model còn thiếu một số metadata chuẩn")
        
        # Show last update
        last_update = aas_model.get('last_update')
        if last_update:
            print(f"\n🕒 Last Update: {last_update}")
        
        print("\n" + "="*70)
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")

if __name__ == "__main__":
    check_aas_model("PC001")
