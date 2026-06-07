def grade_quiz(questions: list, user_answers: dict) -> dict:
    total = len(questions)
    details = []
    correct = 0

    for question in questions:
        question_id = question.get("id")
        user_answer = user_answers.get(question_id, "")
        correct_answer = question.get("answer", "")
        is_correct = user_answer == correct_answer

        if is_correct:
            correct += 1

        details.append(
            {
                "id": question_id,
                "question": question.get("question", ""),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "options": question.get("options", {}),
            }
        )

    wrong = total - correct
    score = round((correct / total) * 10, 2) if total else 0.0

    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "score": score,
        "details": details,
    }
