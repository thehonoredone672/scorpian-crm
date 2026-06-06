import os
import django

# 1. Setup Django environment so we can access our settings/.env variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from database.mongodb_client import db

def run_connection_test():
    try:
        # 2. Send a ping to confirm a successful connection to the cluster
        db.command('ping')
        print("✅ SUCCESS: Successfully connected to MongoDB Atlas Cloud Database!")
        print(f"✅ Connected to Database Name: {db.name}")
        
        # 3. Test Write Operation
        test_collection = db['connection_tests']
        insert_result = test_collection.insert_one({"status": "Cloud integration active", "platform": "Windows"})
        print(f"✅ Write Test Passed! Inserted Document ID: {insert_result.inserted_id}")
        
        # 4. Clean up (Delete the test document)
        test_collection.delete_one({"_id": insert_result.inserted_id})
        print("✅ Cleanup Test Passed! Document removed.")
        
    except Exception as e:
        print(f"❌ ERROR: Could not connect to MongoDB Atlas.")
        print(f"Details: {e}")

if __name__ == "__main__":
    run_connection_test()