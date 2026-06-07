from pathlib import Path

import streamlit as st

from src.quiz_loader import randomize_questions
from src.quiz_sets import get_vocabulary_file_options
from src.vocabulary_utils import is_correct_vocabulary_answer, load_vocabulary


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


st.set_page_config(page_title="Hoc tu vung")
st.title("Hoc tu vung")

vocabulary_file_options = get_vocabulary_file_options(DATA_DIR)
selected_vocabulary_name = st.selectbox(
    "Bo tu vung",
    list(vocabulary_file_options.keys()),
)
selected_vocabulary_file = vocabulary_file_options[selected_vocabulary_name]
vocabulary_items = load_vocabulary(str(selected_vocabulary_file))

if not vocabulary_items:
    st.warning("Bo tu vung nay chua co du lieu. Hay them tu vung truoc khi hoc.")
    st.stop()

practice_mode = st.radio(
    "Kieu hoc",
    [
        "Hien tieng Anh, nhap nghia tieng Viet",
        "Hien nghia tieng Viet, nhap tieng Anh",
    ],
)

vocabulary_ids = tuple(item.get("id") for item in vocabulary_items)
selected_vocabulary_file_name = selected_vocabulary_file.name

if (
    "vocabulary_ids" not in st.session_state
    or st.session_state.get("vocabulary_file_name") != selected_vocabulary_file_name
    or st.session_state.vocabulary_ids != vocabulary_ids
    or st.session_state.get("vocabulary_practice_mode") != practice_mode
):
    st.session_state.vocabulary_file_name = selected_vocabulary_file_name
    st.session_state.vocabulary_ids = vocabulary_ids
    st.session_state.vocabulary_practice_mode = practice_mode
    st.session_state.vocabulary_index = 0
    st.session_state.vocabulary_items = randomize_questions(vocabulary_items)
    st.session_state.vocabulary_checked = False

if st.button("Doi tu khac"):
    st.session_state.vocabulary_index = (
        st.session_state.vocabulary_index + 1
    ) % len(st.session_state.vocabulary_items)
    st.session_state.vocabulary_checked = False

current_item = st.session_state.vocabulary_items[st.session_state.vocabulary_index]

if practice_mode == "Hien tieng Anh, nhap nghia tieng Viet":
    prompt = current_item.get("english", "")
    correct_answer = current_item.get("vietnamese", "")
    input_label = "Nhap nghia tieng Viet"
else:
    prompt = current_item.get("vietnamese", "")
    correct_answer = current_item.get("english", "")
    input_label = "Nhap tu tieng Anh"

st.header(prompt)

with st.form("vocabulary_practice_form"):
    user_answer = st.text_input(input_label)
    submitted = st.form_submit_button("Kiem tra")

if submitted:
    st.session_state.vocabulary_checked = True
    st.session_state.vocabulary_user_answer = user_answer

if st.session_state.get("vocabulary_checked"):
    checked_answer = st.session_state.get("vocabulary_user_answer", "")
    if is_correct_vocabulary_answer(checked_answer, correct_answer):
        st.success("Dung.")
    else:
        st.error("Sai.")
        st.write(f"Dap an dung: {correct_answer}")
