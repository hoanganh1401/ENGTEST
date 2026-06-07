from pathlib import Path

import streamlit as st

from src.quiz_engine import grade_quiz
from src.quiz_loader import load_questions, randomize_questions
from src.quiz_sets import get_quiz_file_options
from src.result_utils import format_score, get_result_message


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


st.set_page_config(page_title="Lam bai kiem tra")
st.title("Lam bai kiem tra")

quiz_file_options = get_quiz_file_options(DATA_DIR)
selected_quiz_name = st.selectbox(
    "Bai kiem tra",
    list(quiz_file_options.keys()),
)
selected_questions_file = quiz_file_options[selected_quiz_name]
loaded_questions = load_questions(str(selected_questions_file))

if not loaded_questions:
    st.warning("Bai kiem tra nay chua co du lieu cau hoi. Hay them cau hoi truoc khi lam bai.")
    st.stop()

QUESTION_COUNT_OPTIONS = [20, 30, 40, 50, 60, 70, 80, 90, 100]
available_count_options = [
    count for count in QUESTION_COUNT_OPTIONS if count <= len(loaded_questions)
]

if not available_count_options:
    available_count_options = [len(loaded_questions)]

selected_question_count = st.selectbox(
    "So luong cau hoi",
    available_count_options,
)

question_ids = tuple(question.get("id") for question in loaded_questions)
selected_quiz_file_name = selected_questions_file.name

if (
    "quiz_question_ids" not in st.session_state
    or st.session_state.get("quiz_file_name") != selected_quiz_file_name
    or st.session_state.quiz_question_ids != question_ids
    or st.session_state.get("quiz_question_count") != selected_question_count
):
    st.session_state.quiz_file_name = selected_quiz_file_name
    st.session_state.quiz_question_ids = question_ids
    st.session_state.quiz_question_count = selected_question_count
    st.session_state.quiz_questions = randomize_questions(loaded_questions)[
        :selected_question_count
    ]

questions = st.session_state.quiz_questions

with st.form("quiz_form"):
    user_answers = {}

    for index, question in enumerate(questions, start=1):
        question_id = question.get("id", index)
        options = question.get("options", {})

        st.subheader(f"Cau {index}: {question.get('question', '')}")
        labels = [
            f"A. {options.get('A', '')}",
            f"B. {options.get('B', '')}",
            f"C. {options.get('C', '')}",
            f"D. {options.get('D', '')}",
        ]
        selected_label = st.radio(
            "Chon dap an",
            labels,
            key=f"{selected_quiz_file_name}_question_{question_id}",
            index=None,
        )
        user_answers[question_id] = selected_label[0] if selected_label else ""

    submitted = st.form_submit_button("Nop bai")

if submitted:
    result = grade_quiz(questions, user_answers)

    st.header("Ket qua")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tong so cau", result["total"])
    col2.metric("So cau dung", result["correct"])
    col3.metric("So cau sai", result["wrong"])
    col4.metric("Diem", format_score(result["score"]))

    st.success(get_result_message(result["score"]))

    st.header("Chi tiet tung cau")
    for index, detail in enumerate(result["details"], start=1):
        status = "Dung" if detail["is_correct"] else "Sai"
        with st.expander(f"Cau {index}: {status}", expanded=True):
            st.write(detail["question"])
            st.write(f"Ban chon: {detail['user_answer'] or 'Chua chon'}")
            st.write(f"Dap an dung: {detail['correct_answer']}")

            if detail["is_correct"]:
                st.success("Ban da tra loi dung.")
            else:
                st.error("Ban da tra loi sai.")

            st.markdown("**Cac dap an:**")
            for key, value in detail["options"].items():
                st.write(f"{key}. {value}")
