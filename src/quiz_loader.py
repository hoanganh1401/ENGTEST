import random
from pathlib import Path
from typing import Any

from src.mongo_utils import get_learning_items_collection, infer_set_type


def load_questions(file_path: str) -> list[dict[str, Any]]:
    """Load learning items from MongoDB by the logical JSONL file name."""
    path = Path(file_path)
    set_type = infer_set_type(file_path)
    collection = get_learning_items_collection()
    documents = collection.find(
        {
            "set_type": set_type,
            "file_name": path.name,
        },
        {"_id": 0, "data": 1},
    ).sort("id", 1)

    return [
        document.get("data", {})
        for document in documents
        if isinstance(document.get("data"), dict)
    ]


def randomize_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return questions in random order without changing the original list."""
    randomized_questions = questions.copy()
    random.shuffle(randomized_questions)
    return randomized_questions


def save_question(file_path: str, question_data: dict) -> None:
    """Save one learning item to MongoDB."""
    path = Path(file_path)
    set_type = infer_set_type(file_path)
    item_id = question_data.get("id")
    collection = get_learning_items_collection()
    collection.update_one(
        {
            "set_type": set_type,
            "file_name": path.name,
            "id": item_id,
        },
        {
            "$set": {
                "set_type": set_type,
                "file_name": path.name,
                "id": item_id,
                "data": question_data,
            }
        },
        upsert=True,
    )


def get_next_question_id(file_path: str) -> int:
    path = Path(file_path)
    set_type = infer_set_type(file_path)
    collection = get_learning_items_collection()
    document = collection.find_one(
        {
            "set_type": set_type,
            "file_name": path.name,
        },
        sort=[("id", -1)],
    )
    if not document:
        return 1

    return int(document.get("id", 0)) + 1
