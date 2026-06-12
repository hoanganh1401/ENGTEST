from pathlib import Path
import os

from src.env_utils import get_env_value


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MONGO_URI = "mongodb://localhost:27017/"
DEFAULT_MONGO_DB = "LANGUAGEDB"


def get_mongo_uri() -> str:
    return (
        os.environ.get("MONGODB_URI")
        or get_env_value(BASE_DIR / ".env", "MONGODB_URI")
        or DEFAULT_MONGO_URI
    )


def get_mongo_db_name() -> str:
    return (
        os.environ.get("MONGODB_DB")
        or get_env_value(BASE_DIR / ".env", "MONGODB_DB")
        or DEFAULT_MONGO_DB
    )


def get_database():
    try:
        from pymongo import MongoClient
    except ImportError as error:
        raise RuntimeError(
            "Chua cai pymongo. Hay chay: pip install -r requirements.txt"
        ) from error

    client = MongoClient(get_mongo_uri(), serverSelectionTimeoutMS=2000)
    client.admin.command("ping")
    return client[get_mongo_db_name()]


def get_learning_items_collection():
    collection = get_database()["learning_items"]
    collection.create_index(
        [("set_type", 1), ("file_name", 1), ("id", 1)],
        unique=True,
    )
    return collection


def get_learning_sets_collection():
    collection = get_database()["learning_sets"]
    collection.create_index(
        [("set_type", 1), ("display_name", 1)],
        unique=True,
    )
    collection.create_index(
        [("set_type", 1), ("file_name", 1)],
        unique=True,
    )
    return collection


def infer_set_type(file_path: str) -> str:
    path = Path(file_path)
    parts = {part.lower() for part in path.parts}
    if "trac_nghiem" in parts:
        return "quiz"
    if "tu_vung" in parts:
        return "vocabulary"
    return "unknown"
