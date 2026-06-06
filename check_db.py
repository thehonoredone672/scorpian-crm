import os
import django
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from database.mongodb_client import db

print('--- FORENSIC DATABASE CHECK ---')
print(f'Currently connected to host: {db.client.HOST}')
print(f'Active Database Target: {db.name}')
print('List of all databases located on this cluster:')
for db_name in db.client.list_database_names():
    print(f' - {db_name}')
