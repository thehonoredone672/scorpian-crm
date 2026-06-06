import os
import pymongo
import certifi
from dotenv import load_dotenv

load_dotenv(override=True)
uri = os.getenv('MONGO_URI')
db_name = os.getenv('MONGO_DB_NAME', 'CRM')

print("🚀 [OPTIMIZATION] Initializing Database Performance Indexing...")

try:
    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where())
    db = client[db_name]
    
    # 1. Optimize Student Query Execution Paths
    print(" -> Indexing 'students' collection...")
    db['students'].create_index([("branch_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
    
    # 2. Optimize Calendar Session Queries
    print(" -> Indexing 'sessions' collection...")
    db['sessions'].create_index([("branch_id", pymongo.ASCENDING), ("session_date", pymongo.ASCENDING)])
    
    # 3. Optimize Financial Ledger Audits
    print(" -> Indexing 'ledger' collection...")
    db['ledger'].create_index([("branch_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
    
    print("✅ DATABASE CONFIGURATION OPTIMIZED FOR ENTERPRISE SCALE!")
except Exception as e:
    print(f"❌ Indexing failed: {e}")