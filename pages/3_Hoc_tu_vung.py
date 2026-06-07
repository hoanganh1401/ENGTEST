from pathlib import Path
import os

import streamlit as st

from src.env_utils import get_env_value
from src.gemini_utils import (
    VOCABULARY_PRONUNCIATION_PROMPT_VERSION,
    get_vocabulary_pronunciation,
)
from src.quiz_loader import randomize_questions
from src.quiz_sets import get_vocabulary_file_options
from src.vocabulary_utils import is_correct_vocabulary_answer, load_vocabulary


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def get_vocabulary_gemini_api_key() -> str:
    api_key = os.environ.get("GEMINI_VOCABULARY_API_KEY", "")
    if api_key:
        return api_key

    api_key = get_env_value(BASE_DIR / ".env", "GEMINI_VOCABULARY_API_KEY")
    if api_key:
        return api_key

    try:
        return st.secrets.get("GEMINI_VOCABULARY_API_KEY", "")
    except Exception:
        return ""


def get_vocabulary_gemini_model() -> str:
    model = os.environ.get("GEMINI_VOCABULARY_MODEL", "")
    if model:
        return model

    model = get_env_value(BASE_DIR / ".env", "GEMINI_VOCABULARY_MODEL")
    if model:
        return model

    try:
        return st.secrets.get("GEMINI_VOCABULARY_MODEL", "")
    except Exception:
        return ""


def infer_pronunciation_language(vocabulary_name: str) -> str:
    normalized_name = vocabulary_name.lower()
    if "tieng trung" in normalized_name:
        return "tieng Trung"
    if "tieng anh" in normalized_name:
        return "tieng Anh"
    return ""


st.set_page_config(page_title="Hoc tu vung")
st.title("Hoc tu vung")

vocabulary_gemini_api_key = get_vocabulary_gemini_api_key()
vocabulary_gemini_model = get_vocabulary_gemini_model()

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
        "Hien ngon ngu, nhap nghia tieng Viet",
        "Hien nghia tieng Viet, nhap ngon ngu",
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
pronunciation_language = infer_pronunciation_language(selected_vocabulary_name)

if practice_mode == "Hien ngon ngu, nhap nghia tieng Viet":
    prompt = current_item.get("english", "")
    correct_answer = current_item.get("vietnamese", "")
    input_label = "Nhap nghia tieng Viet"
else:
    prompt = current_item.get("vietnamese", "")
    correct_answer = current_item.get("english", "")
    input_label = "Nhap tu tieng Anh"

st.header(prompt)

pronunciation_word = current_item.get("english", "").strip()
pronunciation_key = (
    f"pronunciation_{selected_vocabulary_file_name}_"
    f"{current_item.get('id', st.session_state.vocabulary_index)}"
)
pronunciation_state_key = (
    f"{pronunciation_key}_{pronunciation_language}_"
    f"{VOCABULARY_PRONUNCIATION_PROMPT_VERSION}_result"
)

if st.button("Xem phien am / pinyin", key=pronunciation_key):
    with st.spinner("Gemini dang tao phien am..."):
        try:
            ok, pronunciation = get_vocabulary_pronunciation(
                api_key=vocabulary_gemini_api_key,
                word=pronunciation_word,
                language=pronunciation_language,
                model=vocabulary_gemini_model,
            )
        except TypeError:
            ok, pronunciation = get_vocabulary_pronunciation(
                api_key=vocabulary_gemini_api_key,
                word=pronunciation_word,
                language=pronunciation_language,
            )

    if ok:
        st.session_state[pronunciation_state_key] = pronunciation
    else:
        st.warning(pronunciation)

if pronunciation_state_key in st.session_state:
    st.info(st.session_state[pronunciation_state_key])

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
