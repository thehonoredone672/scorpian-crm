import os
import pymongo
import certifi
from dotenv import load_dotenv

# FORCE override of any stuck Windows environment variables
load_dotenv(override=True)

class MongoDBClient:
    """
    Thread-safe Singleton connection pool manager for MongoDB Atlas.
    """
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            
            mongo_uri = os.getenv("MONGO_URI")
            db_name = os.getenv("MONGO_DB_NAME", "CRM")
            
            if not mongo_uri:
                raise ValueError("CRITICAL: MONGO_URI is missing from environment variables!")
                
            # --- DIAGNOSTIC LOG ---
            print(f"\n🔥 [SYSTEM BOOT] Forcing Atlas Cloud Connection via: {mongo_uri[:22]}...\n")
            # ----------------------

            cls._client = pymongo.MongoClient(
                mongo_uri,
                tlsCAFile=certifi.where(),
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                retryWrites=True,
                serverSelectionTimeoutMS=5000 # Fail fast if cloud is unreachable
            )
            cls._db = cls._client[db_name]
        return cls._instance

    @property
    def db(self):
        return self._db

mongo_manager = MongoDBClient()
db = mongo_manager.db