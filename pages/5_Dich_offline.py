import importlib
import html

import streamlit as st

from src import offline_translate_utils


offline_translate_utils = importlib.reload(offline_translate_utils)


@st.cache_resource(show_spinner=False)
def get_cached_language_options():
    return offline_translate_utils.get_language_options()


st.set_page_config(page_title="Dich offline", layout="wide")
st.title("Dich offline")

st.markdown(
    """
    <style>
    .translate-surface textarea {
        min-height: 260px !important;
        font-size: 1.05rem !important;
        line-height: 1.5 !important;
    }
    .translate-result {
        min-height: 260px;
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 8px;
        padding: 0.85rem;
        white-space: pre-wrap;
        font-size: 1.05rem;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

language_options = get_cached_language_options()

if not language_options:
    st.warning(
        "Chua co ngon ngu nao duoc cai cho Argos Translate, hoac chua cai thu vien argostranslate."
    )
else:
    source_col, action_col, target_col = st.columns([1, 0.12, 1])

    source_labels = list(language_options.keys())
    source_label = source_col.selectbox(
        "Ngon ngu nguon",
        source_labels,
        key="offline_source_language",
    )
    source_language = language_options[source_label]
    target_options = offline_translate_utils.get_target_language_options(source_language)

    if not target_options:
        target_col.warning("Chua co goi dich di tu ngon ngu nay.")
    else:
        target_labels = list(target_options.keys())
        target_label = target_col.selectbox(
            "Ngon ngu dich",
            target_labels,
            key="offline_target_language",
        )
        target_language = target_options[target_label]

        if action_col.button("⇄", help="Dao chieu neu cap dich nguoc da duoc cai"):
            reverse_source = f"{target_language.name} ({target_language.code})"
            reverse_targets = offline_translate_utils.get_target_language_options(
                target_language
            )
            reverse_target = f"{source_language.name} ({source_language.code})"

            if reverse_source in language_options and reverse_target in reverse_targets:
                st.session_state.offline_source_language = reverse_source
                st.session_state.offline_target_language = reverse_target
                st.session_state.offline_translated_text = ""
                st.rerun()
            else:
                st.warning("Chua cai goi dich nguoc cho cap ngon ngu nay.")

        input_col, output_col = st.columns(2)
        with input_col:
            st.markdown('<div class="translate-surface">', unsafe_allow_html=True)
            source_text = st.text_area(
                "Van ban can dich",
                key="offline_source_text",
                placeholder="Nhap van ban...",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with output_col:
            translated_text = st.session_state.get("offline_translated_text", "")
            escaped_translated_text = html.escape(translated_text)
            st.markdown(
                f'<div class="translate-result">{escaped_translated_text}</div>',
                unsafe_allow_html=True,
            )

        button_col, clear_col = st.columns([0.15, 0.85])
        if button_col.button("Dich"):
            ok, translated_text = offline_translate_utils.translate_text(
                source_text,
                source_language,
                target_language,
            )
            if ok:
                st.session_state.offline_translated_text = translated_text
                st.rerun()
            else:
                st.warning(translated_text)

        if clear_col.button("Xoa"):
            st.session_state.offline_source_text = ""
            st.session_state.offline_translated_text = ""
            st.rerun()

st.divider()
st.subheader("Cai goi ngon ngu offline")
st.write(
    "Tai truoc file .argosmodel khi co internet, sau do upload tai day de dung offline."
)
uploaded_model = st.file_uploader("File .argosmodel", type=["argosmodel"])
if st.button("Cai goi ngon ngu"):
    ok, message = offline_translate_utils.install_argos_model(uploaded_model)
    if ok:
        st.success(message)
        get_cached_language_options.clear()
        st.rerun()
    else:
        st.warning(message)
