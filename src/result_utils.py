def format_score(score: float) -> str:
    return f"{score:.2f}/10"


def get_result_message(score: float) -> str:
    if score >= 8:
        return "Rat tot"
    if score >= 6.5:
        return "Kha"
    if score >= 5:
        return "Trung binh"
    return "Can on tap them"
