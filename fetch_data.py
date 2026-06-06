import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from database.mongodb_client import db

print('--- FETCHING CLOUD DATA ---')
try:
    # Get the actual replica set nodes, bypassing the 'localhost' SRV illusion
    nodes = db.client.nodes
    print(f'Active Cloud Nodes: {nodes}')
    
    branches = db['branches'].find()
    print('\n--- YOUR BRANCHES ---')
    for b in branches:
        print(f"Name: {b.get('name')} | Code: {b.get('branch_code')} | Status: {b.get('status')}")
        
except Exception as e:
    print(f'Error fetching data: {e}')
