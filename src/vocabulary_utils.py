from typing import Any

from src.quiz_loader import load_questions, save_question


def load_vocabulary(file_path: str) -> list[dict[str, Any]]:
    return load_questions(file_path)


def save_vocabulary_item(file_path: str, vocabulary_data: dict[str, Any]) -> None:
    save_question(file_path, vocabulary_data)


def validate_vocabulary_data(english: str, vietnamese: str) -> tuple[bool, str]:
    if not english or not english.strip():
        return False, "Tu tieng Anh khong duoc de trong."

    if not vietnamese or not vietnamese.strip():
        return False, "Nghia tieng Viet khong duoc de trong."

    return True, "Hop le"


def normalize_answer(value: str) -> str:
    return " ".join(value.strip().lower().split())


def is_correct_vocabulary_answer(user_answer: str, correct_answer: str) -> bool:
    return normalize_answer(user_answer) == normalize_answer(correct_answer)
