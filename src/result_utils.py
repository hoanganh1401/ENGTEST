def format_score(score: float) -> str:
    return f"{score:.2f}/10"


def get_result_message(score: float) -> str:
    if score >= 8:
        return "Rất tốt"
    if score >= 6.5:
        return "Khá"
    if score >= 5:
        return "Trung bình"
    return "Cần ôn tập thêm"
