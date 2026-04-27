"""
Verify MongoDB Atlas - Kiểm tra kết nối và dữ liệu trong MongoDB
Chạy: python verify_mongodb.py
"""
import os
import sys
from datetime import datetime

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from pymongo import MongoClient
except ImportError:
    print("❌ Chưa cài pymongo. Chạy: pip install pymongo[srv]")
    sys.exit(1)

# Cấu hình
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://sa:Admin%40123@cluster0.wtpp0cf.mongodb.net/DigitalTwinDB?retryWrites=true&w=majority")
DB_NAME = os.getenv("MONGODB_DB_NAME", "DigitalTwinDB")

def main():
    print("\n" + "=" * 60)
    print("🔍 KIỂM TRA MONGODB ATLAS")
    print("=" * 60)
    print(f"URI: {MONGODB_URI[:50]}...")
    print(f"Database: {DB_NAME}")
    print()

    try:
        # Kết nối
        print("Đang kết nối MongoDB Atlas...")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        client.server_info()  # Test connection
        print("✅ Kết nối MongoDB Atlas thành công!\n")

        db = client[DB_NAME]

        # Liệt kê collections
        collections = db.list_collection_names()
        print(f"📂 Số collections: {len(collections)}")
        print("-" * 40)

        for col_name in sorted(collections):
            col = db[col_name]
            count = col.count_documents({})
            print(f"  📄 {col_name}: {count} documents")

            # Hiển thị mẫu cho các collection quan trọng
            if count > 0 and "aas" in col_name.lower():
                sample = col.find_one()
                if sample:
                    # Hiển thị một số field quan trọng
                    print(f"      └── Sample fields: {list(sample.keys())[:6]}...")
                    if 'idShort' in sample:
                        print(f"      └── idShort: {sample['idShort']}")
                    if 'id' in sample:
                        print(f"      └── id: {sample['id'][:60]}...")

        print("\n" + "=" * 60)
        print("📊 TÓM TẮT")
        print("=" * 60)

        # Đếm AAS shells
        shells_col = db.get_collection("aasEnvironment-shells") if "aasEnvironment-shells" in collections else None
        submodels_col = db.get_collection("aasEnvironment-submodels") if "aasEnvironment-submodels" in collections else None

        if shells_col:
            shell_count = shells_col.count_documents({})
            print(f"  🏗️  AAS Shells: {shell_count}")
            if shell_count > 0:
                for shell in shells_col.find():
                    id_short = shell.get('idShort', 'N/A')
                    aas_id = shell.get('id', 'N/A')
                    print(f"      ├── {id_short} ({aas_id[:50]}...)")
        else:
            print("  ⚠️  Collection 'aasEnvironment-shells' chưa tồn tại")
            print("      → BaSyx Server chưa chạy hoặc chưa có thiết bị nào được tạo")

        if submodels_col:
            sm_count = submodels_col.count_documents({})
            print(f"  📋 Submodels: {sm_count}")
            if sm_count > 0:
                for sm in submodels_col.find():
                    id_short = sm.get('idShort', 'N/A')
                    sm_id = sm.get('id', 'N/A')
                    elements_count = len(sm.get('submodelElements', []))
                    print(f"      ├── {id_short} ({elements_count} elements)")
        else:
            print("  ⚠️  Collection 'aasEnvironment-submodels' chưa tồn tại")

        # Kiểm tra collections do DataBridge tạo
        databridge_collections = ["telemetry_history", "pc_status", "aas_models", "events", "iot_data_log"]
        found_db_cols = [c for c in databridge_collections if c in collections]
        if found_db_cols:
            print(f"\n  🌉 DataBridge collections: {', '.join(found_db_cols)}")
            for col_name in found_db_cols:
                count = db[col_name].count_documents({})
                print(f"      ├── {col_name}: {count} documents")
        else:
            print(f"\n  ℹ️  Chưa có DataBridge collections (telemetry_history, iot_data_log...)")
            print(f"      → Sẽ được tạo khi dữ liệu IoT bắt đầu gửi vào")

        print("\n" + "=" * 60)
        print(f"✅ Kiểm tra hoàn tất lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
        print("=" * 60 + "\n")

        client.close()

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("\nKiểm tra lại:")
        print("  1. MONGODB_URI trong file .env có đúng không?")
        print("  2. IP của máy bạn đã được whitelist trong MongoDB Atlas chưa?")
        print("  3. Internet có ổn không?")
        sys.exit(1)


if __name__ == "__main__":
    main()
