from pathlib import Path
import os

import streamlit as st

from src.env_utils import get_env_value
from src.gemini_utils import EXPLANATION_PROMPT_VERSION, explain_wrong_answer
from src.quiz_engine import grade_quiz
from src.quiz_loader import load_questions, randomize_questions
from src.quiz_sets import get_quiz_file_options
from src.result_utils import format_score, get_result_message


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def get_gemini_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        return api_key

    api_key = get_env_value(BASE_DIR / ".env", "GEMINI_API_KEY")
    if api_key:
        return api_key

    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def get_gemini_model() -> str:
    model = os.environ.get("GEMINI_MODEL", "")
    if model:
        return model

    model = get_env_value(BASE_DIR / ".env", "GEMINI_MODEL")
    if model:
        return model

    try:
        return st.secrets.get("GEMINI_MODEL", "")
    except Exception:
        return ""


def render_question_details(
    question_details: list[tuple[int, dict]],
    selected_quiz_file_name: str,
    gemini_api_key: str,
    gemini_model: str,
    view_key: str,
) -> None:
    if not question_details:
        st.info("Không có câu hỏi nào.")
        return

    for index, detail in question_details:
        status = "Đúng" if detail["is_correct"] else "Sai"
        with st.expander(f"Câu {index}: {status}", expanded=True):
            st.write(detail["question"])
            st.write(f"Bạn chọn: {detail['user_answer'] or 'Chưa chọn'}")
            st.write(f"Đáp án đúng: {detail['correct_answer']}")
            if detail["is_correct"]:
                st.success("Bạn đã trả lời đúng.")
            else:
                st.error("Bạn đã trả lời sai.")

            st.markdown("**Các đáp án:**")
            for key, value in detail["options"].items():
                st.write(f"{key}. {value}")

            if not detail["is_correct"]:
                explanation_key = (
                    f"explain_{selected_quiz_file_name}_{detail['id']}_{index}"
                )
                explain_button_key = f"{view_key}_{explanation_key}"
                explanation_state_key = (
                    f"{explanation_key}_{EXPLANATION_PROMPT_VERSION}_result"
                )
                if st.button("AI giải thích đáp án sai", key=explain_button_key):
                    with st.spinner("Gemini đang giải thích..."):
                        ok, explanation = explain_wrong_answer(
                            api_key=gemini_api_key,
                            question=detail["question"],
                            options=detail["options"],
                            user_answer=detail["user_answer"],
                            correct_answer=detail["correct_answer"],
                            model=gemini_model,
                        )

                    if ok:
                        st.session_state[explanation_state_key] = explanation
                    else:
                        st.warning(explanation)

                if explanation_state_key in st.session_state:
                    st.info(st.session_state[explanation_state_key])


def reset_quiz_attempt(
    selected_quiz_file_name: str,
    loaded_questions: list[dict],
    selected_question_count: int,
) -> None:
    clear_quiz_attempt_state(selected_quiz_file_name, loaded_questions)
    st.session_state.quiz_attempt_id = st.session_state.get("quiz_attempt_id", 0) + 1
    st.session_state.quiz_questions = randomize_questions(loaded_questions)[
        :selected_question_count
    ]
    st.session_state.quiz_result_file_name = selected_quiz_file_name
    st.session_state.quiz_result_question_count = selected_question_count


def clear_quiz_attempt_state(
    selected_quiz_file_name: str,
    loaded_questions: list[dict],
) -> None:
    for question in loaded_questions:
        question_id = question.get("id")
        st.session_state.pop(f"{selected_quiz_file_name}_question_{question_id}", None)

    for state_key in list(st.session_state.keys()):
        if (
            state_key.startswith("quiz_result")
            or f"explain_{selected_quiz_file_name}_" in state_key
            or state_key.startswith(f"{selected_quiz_file_name}_attempt_")
        ):
            st.session_state.pop(state_key, None)


st.set_page_config(page_title="Làm bài kiểm tra")
st.title("Làm bài kiểm tra")

gemini_api_key = get_gemini_api_key()
gemini_model = get_gemini_model()

quiz_file_options = get_quiz_file_options(DATA_DIR)
selected_quiz_name = st.selectbox(
    "Bài kiểm tra",
    list(quiz_file_options.keys()),
)
selected_questions_file = quiz_file_options[selected_quiz_name]
loaded_questions = load_questions(str(selected_questions_file))

if not loaded_questions:
    st.warning("Bài kiểm tra này chưa có dữ liệu câu hỏi. Hãy thêm câu hỏi trước khi làm bài.")
    st.stop()

QUESTION_COUNT_OPTIONS = [20, 30, 40, 50, 60, 70, 80, 90, 100]
available_count_options = [
    count for count in QUESTION_COUNT_OPTIONS if count <= len(loaded_questions)
]

if not available_count_options:
    available_count_options = [len(loaded_questions)]

selected_question_count = st.selectbox(
    "Số lượng câu hỏi",
    available_count_options,
)

question_ids = tuple(question.get("id") for question in loaded_questions)
selected_quiz_file_name = selected_questions_file.name

quiz_settings_changed = (
    "quiz_question_ids" not in st.session_state
    or st.session_state.get("quiz_file_name") != selected_quiz_file_name
    or st.session_state.quiz_question_ids != question_ids
    or st.session_state.get("quiz_question_count") != selected_question_count
)

if quiz_settings_changed:
    clear_quiz_attempt_state(selected_quiz_file_name, loaded_questions)
    st.session_state.quiz_attempt_id = st.session_state.get("quiz_attempt_id", 0) + 1
    st.session_state.quiz_file_name = selected_quiz_file_name
    st.session_state.quiz_question_ids = question_ids
    st.session_state.quiz_question_count = selected_question_count
    st.session_state.quiz_questions = randomize_questions(loaded_questions)[
        :selected_question_count
    ]

questions = st.session_state.quiz_questions
quiz_attempt_id = st.session_state.get("quiz_attempt_id", 0)

with st.form("quiz_form"):
    user_answers = {}

    for index, question in enumerate(questions, start=1):
        question_id = question.get("id", index)
        options = question.get("options", {})

        st.subheader(f"Câu {index}: {question.get('question', '')}")
        labels = [
            f"A. {options.get('A', '')}",
            f"B. {options.get('B', '')}",
            f"C. {options.get('C', '')}",
            f"D. {options.get('D', '')}",
        ]
        selected_label = st.radio(
            "Chọn đáp án",
            labels,
            key=(
                f"{selected_quiz_file_name}_attempt_{quiz_attempt_id}_"
                f"question_{question_id}"
            ),
            index=None,
        )
        user_answers[question_id] = selected_label[0] if selected_label else ""

    submitted = st.form_submit_button("Nộp bài")

if submitted:
    st.session_state.quiz_result = grade_quiz(questions, user_answers)
    st.session_state.quiz_result_file_name = selected_quiz_file_name
    st.session_state.quiz_result_question_count = selected_question_count

if (
    "quiz_result" in st.session_state
    and st.session_state.get("quiz_result_file_name") == selected_quiz_file_name
    and st.session_state.get("quiz_result_question_count") == selected_question_count
):
    result = st.session_state.quiz_result
    st.header("Kết quả")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số câu", result["total"])
    col2.metric("Số câu đúng", result["correct"])
    col3.metric("Số câu sai", result["wrong"])
    col4.metric("Điểm", format_score(result["score"]))

    st.success(get_result_message(result["score"]))
    if st.button("Làm lại bài"):
        reset_quiz_attempt(
            selected_quiz_file_name,
            loaded_questions,
            selected_question_count,
        )
        st.rerun()

    st.header("Chi tiết kết quả từng câu hỏi")
    indexed_details = list(enumerate(result["details"], start=1))
    correct_details = [
        (index, detail)
        for index, detail in indexed_details
        if detail["is_correct"]
    ]
    wrong_details = [
        (index, detail)
        for index, detail in indexed_details
        if not detail["is_correct"]
    ]

    correct_tab, wrong_tab, all_tab = st.tabs(
        [
            f"Câu đúng ({len(correct_details)})",
            f"Câu sai ({len(wrong_details)})",
            f"Toàn bộ bài kiểm tra ({len(indexed_details)})",
        ]
    )

    with correct_tab:
        render_question_details(
            correct_details,
            selected_quiz_file_name,
            gemini_api_key,
            gemini_model,
            "correct",
        )

    with wrong_tab:
        render_question_details(
            wrong_details,
            selected_quiz_file_name,
            gemini_api_key,
            gemini_model,
            "wrong",
        )

    with all_tab:
        render_question_details(
            indexed_details,
            selected_quiz_file_name,
            gemini_api_key,
            gemini_model,
            "all",
        )
