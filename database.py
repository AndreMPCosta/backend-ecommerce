# from motor.motor_asyncio import AsyncIOMotorClient
# from odmantic import AIOEngine
from os import getenv

from mongoengine import connect

from config import backend_ip

print(f'Starting Engine in {getenv("ENVIRONMENT")}')

MONGO_DATABASE_URL = f"mongodb://user:password@{backend_ip}:27017/" \
    if getenv('ENVIRONMENT') == 'dev' else \
    "mongodb://user:password@localhost:27017/"
MONGO_DATABASE = "shop"

# client = AsyncIOMotorClient(MONGO_DATABASE_URL)
# print('Engine Started')
# engine = AIOEngine(motor_client=client, database=MONGO_DATABASE)

db = connect(host=f'{MONGO_DATABASE_URL}{MONGO_DATABASE}?authSource=admin')

# Base.metadata.create_all(bind=eng)

# metadata = MetaData()
