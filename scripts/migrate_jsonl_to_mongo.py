import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.mongo_utils import get_learning_sets_collection
from src.quiz_loader import save_question
from src.quiz_sets import QUIZ_FILES, VOCABULARY_FILES


DATA_DIR = BASE_DIR / "data"


def load_jsonl(file_path: Path) -> list[dict]:
    if not file_path.exists():
        return []

    items = []
    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(item, dict):
                items.append(item)

    return items


def register_custom_set(set_type: str, display_name: str, file_name: str) -> None:
    collection = get_learning_sets_collection()
    collection.update_one(
        {
            "set_type": set_type,
            "display_name": display_name,
        },
        {
            "$set": {
                "set_type": set_type,
                "display_name": display_name,
                "file_name": file_name,
            }
        },
        upsert=True,
    )


def migrate_directory(
    set_type: str,
    target_dir: Path,
    known_files: dict[str, str],
) -> int:
    migrated_count = 0
    known_file_names = set(known_files.values())

    for display_name, file_name in known_files.items():
        file_path = target_dir / file_name
        for item in load_jsonl(file_path):
            save_question(str(file_path), item)
            migrated_count += 1

    for file_path in sorted(target_dir.glob("*.jsonl")):
        if file_path.name in known_file_names:
            continue

        display_name = file_path.stem.replace("_", " ").strip().title()
        register_custom_set(set_type, display_name, file_path.name)
        for item in load_jsonl(file_path):
            save_question(str(file_path), item)
            migrated_count += 1

    return migrated_count


def main() -> None:
    quiz_count = migrate_directory(
        "quiz",
        DATA_DIR / "trac_nghiem",
        QUIZ_FILES,
    )
    vocabulary_count = migrate_directory(
        "vocabulary",
        DATA_DIR / "tu_vung",
        VOCABULARY_FILES,
    )
    print(f"Migrated quiz items: {quiz_count}")
    print(f"Migrated vocabulary items: {vocabulary_count}")


if __name__ == "__main__":
    main()
