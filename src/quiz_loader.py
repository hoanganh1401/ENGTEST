import json
import random
from pathlib import Path
from typing import Any


def _ensure_file(file_path: str) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def load_questions(file_path: str) -> list[dict[str, Any]]:
    """Load questions from a JSONL file, skipping invalid empty lines safely."""
    path = _ensure_file(file_path)
    questions: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(item, dict):
                questions.append(item)

    return questions


def randomize_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return questions in random order without changing the original list."""
    randomized_questions = questions.copy()
    random.shuffle(randomized_questions)
    return randomized_questions


def save_question(file_path: str, question_data: dict) -> None:
    """Append one question to the end of a JSONL file."""
    path = _ensure_file(file_path)

    with path.open("a", encoding="utf-8") as file:
        json.dump(question_data, file, ensure_ascii=False)
        file.write("\n")


def get_next_question_id(file_path: str) -> int:
    questions = load_questions(file_path)
    if not questions:
        return 1

    ids = [item.get("id", 0) for item in questions if isinstance(item.get("id"), int)]
    return max(ids, default=0) + 1
