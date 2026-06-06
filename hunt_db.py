import os
import pymongo
import certifi
from dotenv import load_dotenv

# The override=True is the magic bullet. It destroys stuck PowerShell variables.
load_dotenv(override=True)

uri = os.getenv('MONGO_URI')

print('--- THE DATA HUNT ---')
print(f'Attempting to connect using URI starting with: {uri[:18]}...')

try:
    # Force the cloud connection using certifi for Windows
    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=7000)
    
    # Ping the database to prove the connection
    client.admin.command('ping')
    print('✅ CLOUD CONNECTION SUCCESSFUL!')
    
    db = client['CRM']
    branches = list(db['branches'].find())
    
    if branches:
        print('\n✅ FOUND DATA IN THE CLOUD!')
        for b in branches:
            print(f" -> {b['name']} ({b['branch_code']})")
    else:
        print('\n❌ DATABASE CONNECTED, BUT IT IS EMPTY.')
        print('Conclusion: Your data was written to your Local Windows PC during the timeout.')
        
except Exception as e:
    print(f'\n❌ CLOUD CONNECTION FAILED: {e}')
    print('You need to whitelist your IP address in MongoDB Atlas!')
