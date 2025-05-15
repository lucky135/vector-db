"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

from pymongo import MongoClient
from os import getenv
from src.api.common.logging.Logger import log

# MongoDB configuration
DB_CONNECTION_URL = getenv("DB_CONNECTION_URL")
DB_NAME = getenv("DB_NAME")

# Initialize the client and database once
client = None
db = None


def get_db_client():
    global client, db
    if client is None or db is None:
        try:
            if not DB_CONNECTION_URL or not DB_NAME:
                raise ValueError(
                    "Database connection URL or name is not set in environment variables."
                )

            client = MongoClient(DB_CONNECTION_URL)
            db = client[DB_NAME]
            log.info("Successfully connected to MongoDB")
        except Exception as error:
            log.error(f"Error connecting to MongoDB: {error}")
            client = None
            db = None
    return db
