from pathlib import Path
import importlib

import streamlit as st

from src.quiz_loader import get_next_question_id, save_question
from src import quiz_sets
from src.quiz_validator import validate_question_data
from src.vocabulary_utils import save_vocabulary_item, validate_vocabulary_data


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
quiz_sets = importlib.reload(quiz_sets)


st.set_page_config(page_title="Thêm câu hỏi và từ vựng")
st.title("Thêm dữ liệu học tập")

quiz_file_options = quiz_sets.get_quiz_file_options(DATA_DIR)
vocabulary_file_options = quiz_sets.get_vocabulary_file_options(DATA_DIR)
data_type = st.radio(
    "Loại dữ liệu muốn thêm",
    ["Câu hỏi trắc nghiệm", "Từ vựng"],
    horizontal=True,
)

if data_type == "Câu hỏi trắc nghiệm":
    if st.button("Tạo bài kiểm tra mới"):
        st.session_state.is_creating_new_quiz = True

    if st.session_state.get("is_creating_new_quiz"):
        if st.button("Hủy tạo bài kiểm tra mới"):
            st.session_state.is_creating_new_quiz = False
            st.rerun()

    with st.form("question_form", clear_on_submit=True):
        new_quiz_name = ""
        selected_quiz_name = ""
        if st.session_state.get("is_creating_new_quiz"):
            new_quiz_name = st.text_input(
                "Tên bài kiểm tra mới",
                placeholder="Vi du: Kiem tra gioi tu",
            )
        else:
            selected_quiz_name = st.selectbox(
                "Bài kiểm tra",
                list(quiz_file_options.keys()),
            )

        question = st.text_area("Nội dung câu hỏi", placeholder="Nhập nội dung câu hỏi...")
        option_a = st.text_input("Đáp án A")
        option_b = st.text_input("Đáp án B")
        option_c = st.text_input("Đáp án C")
        option_d = st.text_input("Đáp án D")
        answer = st.selectbox("Đáp án đúng", ["A", "B", "C", "D"])
        submitted = st.form_submit_button("Lưu câu hỏi")

    if submitted:
        options = {
            "A": option_a.strip(),
            "B": option_b.strip(),
            "C": option_c.strip(),
            "D": option_d.strip(),
        }
        is_valid, message = validate_question_data(question, options, answer)

        if not is_valid:
            st.error(message)
        else:
            if st.session_state.get("is_creating_new_quiz"):
                try:
                    selected_questions_file = quiz_sets.create_quiz_file_option(
                        DATA_DIR,
                        new_quiz_name,
                    )
                    saved_quiz_name = " ".join(new_quiz_name.strip().split())
                except ValueError as error:
                    st.error(str(error))
                    st.stop()
            else:
                selected_questions_file = quiz_file_options[selected_quiz_name]
                saved_quiz_name = selected_quiz_name

            question_data = {
                "id": get_next_question_id(str(selected_questions_file)),
                "question": question.strip(),
                "options": options,
                "answer": answer,
            }
            save_question(str(selected_questions_file), question_data)
            st.success(f"Lưu câu hỏi thành công vào {saved_quiz_name}.")
            st.session_state.is_creating_new_quiz = False
else:
    if st.button("Tạo bộ từ vựng mới"):
        st.session_state.is_creating_new_vocabulary = True

    if st.session_state.get("is_creating_new_vocabulary"):
        if st.button("Hủy tạo bộ từ vựng mới"):
            st.session_state.is_creating_new_vocabulary = False
            st.rerun()

    with st.form("vocabulary_form", clear_on_submit=True):
        new_vocabulary_name = ""
        selected_vocabulary_name = ""
        if st.session_state.get("is_creating_new_vocabulary"):
            new_vocabulary_name = st.text_input(
                "Tên bộ từ vựng mới",
                placeholder="Vi du: Tu vung nha hang",
            )
        else:
            selected_vocabulary_name = st.selectbox(
                "Bộ từ vựng",
                list(vocabulary_file_options.keys()),
            )

        english = st.text_input("Từ tiếng Anh")
        vietnamese = st.text_input("Nghĩa tiếng Việt")

        submitted = st.form_submit_button("Lưu từ vựng")

    if submitted:
        is_valid, message = validate_vocabulary_data(english, vietnamese)

        if not is_valid:
            st.error(message)
        else:
            if st.session_state.get("is_creating_new_vocabulary"):
                try:
                    selected_vocabulary_file = quiz_sets.create_vocabulary_file_option(
                        DATA_DIR,
                        new_vocabulary_name,
                    )
                    saved_vocabulary_name = " ".join(new_vocabulary_name.strip().split())
                except ValueError as error:
                    st.error(str(error))
                    st.stop()
            else:
                selected_vocabulary_file = vocabulary_file_options[selected_vocabulary_name]
                saved_vocabulary_name = selected_vocabulary_name

            vocabulary_data = {
                "id": get_next_question_id(str(selected_vocabulary_file)),
                "english": english.strip(),
                "vietnamese": vietnamese.strip(),
            }
            save_vocabulary_item(str(selected_vocabulary_file), vocabulary_data)
            st.success(f"Lưu từ vựng thành công vào {saved_vocabulary_name}.")
            st.session_state.is_creating_new_vocabulary = False
