from pathlib import Path

import streamlit as st

from src.quiz_loader import get_next_question_id, save_question
from src.quiz_sets import get_quiz_file_options, get_vocabulary_file_options
from src.quiz_validator import validate_question_data
from src.vocabulary_utils import save_vocabulary_item, validate_vocabulary_data


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


st.set_page_config(page_title="Them cau hoi")
st.title("Them du lieu hoc tap")

quiz_file_options = get_quiz_file_options(DATA_DIR)
vocabulary_file_options = get_vocabulary_file_options(DATA_DIR)
data_type = st.radio(
    "Loai du lieu",
    ["Cau hoi trac nghiem", "Tu vung"],
    horizontal=True,
)

if data_type == "Cau hoi trac nghiem":
    with st.form("question_form", clear_on_submit=True):
        selected_quiz_name = st.selectbox(
            "Bai kiem tra",
            list(quiz_file_options.keys()),
        )
        question = st.text_area("Noi dung cau hoi", placeholder="Nhap noi dung cau hoi...")
        option_a = st.text_input("Dap an A")
        option_b = st.text_input("Dap an B")
        option_c = st.text_input("Dap an C")
        option_d = st.text_input("Dap an D")
        answer = st.selectbox("Dap an dung", ["A", "B", "C", "D"])

        submitted = st.form_submit_button("Luu cau hoi")

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
            selected_questions_file = quiz_file_options[selected_quiz_name]
            question_data = {
                "id": get_next_question_id(str(selected_questions_file)),
                "question": question.strip(),
                "options": options,
                "answer": answer,
            }
            save_question(str(selected_questions_file), question_data)
            st.success(f"Luu cau hoi thanh cong vao {selected_quiz_name}.")
else:
    with st.form("vocabulary_form", clear_on_submit=True):
        selected_vocabulary_name = st.selectbox(
            "Bo tu vung",
            list(vocabulary_file_options.keys()),
        )
        english = st.text_input("Tu tieng Anh")
        vietnamese = st.text_input("Nghia tieng Viet")

        submitted = st.form_submit_button("Luu tu vung")

    if submitted:
        is_valid, message = validate_vocabulary_data(english, vietnamese)

        if not is_valid:
            st.error(message)
        else:
            selected_vocabulary_file = vocabulary_file_options[selected_vocabulary_name]
            vocabulary_data = {
                "id": get_next_question_id(str(selected_vocabulary_file)),
                "english": english.strip(),
                "vietnamese": vietnamese.strip(),
            }
            save_vocabulary_item(str(selected_vocabulary_file), vocabulary_data)
            st.success(f"Luu tu vung thanh cong vao {selected_vocabulary_name}.")
