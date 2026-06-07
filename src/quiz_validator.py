VALID_ANSWERS = {"A", "B", "C", "D"}


def validate_question_data(question: str, options: dict, answer: str) -> tuple[bool, str]:
    if not question or not question.strip():
        return False, "Cau hoi khong duoc de trong."

    for key in ("A", "B", "C", "D"):
        value = options.get(key, "")
        if not value or not str(value).strip():
            return False, f"Dap an {key} khong duoc de trong."

    if answer not in VALID_ANSWERS:
        return False, "Dap an dung phai la A, B, C hoac D."

    return True, "Hop le"
