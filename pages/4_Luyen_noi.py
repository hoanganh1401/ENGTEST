from pathlib import Path
import importlib
import os

import streamlit as st

from src.env_utils import get_env_value
from src import gemini_utils
from src import speaking_utils
from src.quiz_loader import randomize_questions
from src.quiz_sets import get_vocabulary_file_options
from src.vocabulary_utils import load_vocabulary


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
gemini_utils = importlib.reload(gemini_utils)
speaking_utils = importlib.reload(speaking_utils)


def get_speaking_gemini_api_key() -> str:
    api_key = os.environ.get("GEMINI_SPEAKING_API_KEY", "")
    if api_key:
        return api_key

    api_key = get_env_value(BASE_DIR / ".env", "GEMINI_SPEAKING_API_KEY")
    if api_key:
        return api_key

    try:
        return st.secrets.get("GEMINI_SPEAKING_API_KEY", "")
    except Exception:
        return ""


def get_speaking_gemini_model() -> str:
    model = os.environ.get("GEMINI_SPEAKING_MODEL", "")
    if model:
        return model

    model = get_env_value(BASE_DIR / ".env", "GEMINI_SPEAKING_MODEL")
    if model:
        return model

    try:
        return st.secrets.get("GEMINI_SPEAKING_MODEL", "")
    except Exception:
        return ""


def get_phonemizer_espeak_library() -> str:
    library_path = os.environ.get("PHONEMIZER_ESPEAK_LIBRARY", "")
    if library_path:
        return library_path

    return get_env_value(BASE_DIR / ".env", "PHONEMIZER_ESPEAK_LIBRARY")


@st.cache_resource(show_spinner=False)
def load_whisper_model(model_size: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model_size, device="cpu", compute_type="int8")


def get_whisper_language(speaking_language: str) -> str:
    if "trung" in speaking_language.lower():
        return "zh"
    if "anh" in speaking_language.lower():
        return "en"
    return ""


def infer_speaking_language(vocabulary_name: str) -> str:
    normalized_name = vocabulary_name.lower()
    if "tieng trung" in normalized_name:
        return "tieng Trung"
    if "tieng anh" in normalized_name:
        return "tieng Anh"
    return "tieng Anh"


def configure_phonemizer_espeak_library(espeak_library_path: str) -> str:
    if not espeak_library_path:
        return ""

    try:
        from phonemizer.backend.espeak.wrapper import EspeakWrapper

        EspeakWrapper.set_library(espeak_library_path)
    except Exception as error:
        return f"Khong cau hinh duoc eSpeak tu .env: {error}"

    return ""


def get_ipa_with_fallback(
    text: str,
    speaking_language: str,
    phonemizer_language: str,
    api_key: str,
    model: str,
    espeak_library_path: str,
) -> tuple[str, str]:
    espeak_note = configure_phonemizer_espeak_library(espeak_library_path)
    try:
        ok_ipa, ipa = speaking_utils.phonemize_to_ipa(
            text,
            language=phonemizer_language,
            espeak_library_path=espeak_library_path,
        )
    except TypeError:
        ok_ipa, ipa = speaking_utils.phonemize_to_ipa(
            text,
            language=phonemizer_language,
        )

    if ok_ipa:
        return ipa, espeak_note

    ok_gemini_ipa, gemini_ipa = gemini_utils.get_speaking_ipa(
        api_key=api_key,
        text=text,
        language=speaking_language,
        model=model,
    )
    if ok_gemini_ipa:
        note = f"Da dung Gemini de tao IPA vi phonemizer gap loi: {ipa}"
        if espeak_note:
            note = f"{espeak_note}. {note}"
        return gemini_ipa, note

    note = f"Khong tao duoc IPA bang phonemizer hoac Gemini. Phonemizer: {ipa}. Gemini: {gemini_ipa}"
    if espeak_note:
        note = f"{espeak_note}. {note}"
    return "", note


def get_pronunciation_with_fallback(
    text: str,
    speaking_language: str,
    phonemizer_language: str,
    api_key: str,
    model: str,
    espeak_library_path: str,
) -> tuple[str, str]:
    pronunciation_system = speaking_utils.get_pronunciation_system(speaking_language)
    if pronunciation_system == "pinyin":
        ok_pinyin, pinyin = speaking_utils.text_to_pinyin(text)
        if ok_pinyin:
            return pinyin, ""

        ok_gemini_pinyin, gemini_pinyin = gemini_utils.get_speaking_pinyin(
            api_key=api_key,
            text=text,
            model=model,
        )
        if ok_gemini_pinyin:
            return gemini_pinyin, f"Da dung Gemini de tao pinyin vi pypinyin gap loi: {pinyin}"

        return "", f"Khong tao duoc pinyin bang pypinyin hoac Gemini. pypinyin: {pinyin}. Gemini: {gemini_pinyin}"

    return get_ipa_with_fallback(
        text=text,
        speaking_language=speaking_language,
        phonemizer_language=phonemizer_language,
        api_key=api_key,
        model=model,
        espeak_library_path=espeak_library_path,
    )


st.set_page_config(page_title="Luyen noi")
st.title("Luyen noi")

speaking_gemini_api_key = get_speaking_gemini_api_key()
speaking_gemini_model = get_speaking_gemini_model()
phonemizer_espeak_library = get_phonemizer_espeak_library()

vocabulary_file_options = get_vocabulary_file_options(DATA_DIR)
selected_vocabulary_name = st.selectbox(
    "Bo tu vung",
    list(vocabulary_file_options.keys()),
)
selected_vocabulary_file = vocabulary_file_options[selected_vocabulary_name]
vocabulary_items = load_vocabulary(str(selected_vocabulary_file))

if not vocabulary_items:
    st.warning("Bo tu vung nay chua co du lieu. Hay them tu vung truoc khi luyen noi.")
    st.stop()

selected_vocabulary_file_name = selected_vocabulary_file.name
vocabulary_ids = tuple(item.get("id") for item in vocabulary_items)

if (
    "speaking_vocabulary_ids" not in st.session_state
    or st.session_state.get("speaking_vocabulary_file_name") != selected_vocabulary_file_name
    or st.session_state.speaking_vocabulary_ids != vocabulary_ids
):
    st.session_state.speaking_vocabulary_file_name = selected_vocabulary_file_name
    st.session_state.speaking_vocabulary_ids = vocabulary_ids
    st.session_state.speaking_index = 0
    st.session_state.speaking_items = randomize_questions(vocabulary_items)

if st.button("Doi tu khac"):
    st.session_state.speaking_index = (
        st.session_state.speaking_index + 1
    ) % len(st.session_state.speaking_items)

current_item = st.session_state.speaking_items[st.session_state.speaking_index]
default_target_text = current_item.get("english", "").strip()
speaking_language = infer_speaking_language(selected_vocabulary_name)
phonemizer_language = speaking_utils.get_phonemizer_language(speaking_language)
pronunciation_system = speaking_utils.get_pronunciation_system(speaking_language)
pronunciation_label = "Pinyin" if pronunciation_system == "pinyin" else "IPA"
whisper_language = get_whisper_language(speaking_language)

if pronunciation_system == "pinyin":
    st.caption("He phien am: pinyin")
else:
    st.caption(f"Ngon ngu IPA: {phonemizer_language}")
target_text = st.text_input("Tu/cau muc tieu", value=default_target_text)
whisper_model_size = st.selectbox(
    "Whisper model",
    ["tiny", "base", "small"],
    index=0,
)
uploaded_audio = st.audio_input("Ghi am giong noi cua ban")

analyze_key = (
    f"speaking_analyze_{selected_vocabulary_file_name}_"
    f"{current_item.get('id', st.session_state.speaking_index)}"
)

if st.button("Phan tich phat am", key=analyze_key):
    if not uploaded_audio:
        st.warning("Hay ghi am truoc khi phan tich.")
    elif not target_text.strip():
        st.warning("Hay nhap tu/cau muc tieu.")
    else:
        with st.spinner("Whisper dang nghe audio..."):
            try:
                whisper_model = load_whisper_model(whisper_model_size)
            except ImportError:
                st.error(
                    "Chua cai faster-whisper. Hay chay: pip install -r requirements.txt"
                )
                st.stop()
            except Exception as error:
                st.error(f"Khong tai duoc Whisper model: {error}")
                st.stop()

            audio_path = speaking_utils.write_uploaded_audio(uploaded_audio)
            ok_transcript, transcript = speaking_utils.transcribe_audio_file(
                whisper_model,
                audio_path,
                language=whisper_language,
            )

        if not ok_transcript:
            st.error(transcript)
            st.stop()

        with st.spinner("Dang tao IPA..."):
            target_ipa, target_ipa_note = get_pronunciation_with_fallback(
                target_text,
                speaking_language=speaking_language,
                phonemizer_language=phonemizer_language,
                api_key=speaking_gemini_api_key,
                model=speaking_gemini_model,
                espeak_library_path=phonemizer_espeak_library,
            )
            spoken_ipa, spoken_ipa_note = get_pronunciation_with_fallback(
                transcript,
                speaking_language=speaking_language,
                phonemizer_language=phonemizer_language,
                api_key=speaking_gemini_api_key,
                model=speaking_gemini_model,
                espeak_library_path=phonemizer_espeak_library,
            )

        if target_ipa_note:
            st.info(target_ipa_note)

        if spoken_ipa_note:
            st.info(spoken_ipa_note)

        with st.spinner("Gemini dang tao feedback..."):
            ok_feedback, feedback = gemini_utils.get_speaking_feedback(
                api_key=speaking_gemini_api_key,
                target_text=target_text,
                transcript=transcript,
                target_ipa=target_ipa,
                spoken_ipa=spoken_ipa,
                pronunciation_label=pronunciation_label,
                model=speaking_gemini_model,
            )

        st.session_state.speaking_result = {
            "prompt_version": gemini_utils.SPEAKING_FEEDBACK_PROMPT_VERSION,
            "target_text": target_text,
            "transcript": transcript,
            "target_ipa": target_ipa,
            "spoken_ipa": spoken_ipa,
            "pronunciation_label": pronunciation_label,
            "feedback_ok": ok_feedback,
            "feedback": feedback,
        }

if "speaking_result" in st.session_state:
    result = st.session_state.speaking_result
    st.subheader("Ket qua")
    st.write(f"Tu/cau muc tieu: {result['target_text']}")
    st.write(f"Whisper nghe duoc: {result['transcript']}")

    if result["target_ipa"]:
        st.write(f"{result.get('pronunciation_label', 'IPA')} muc tieu: {result['target_ipa']}")

    if result["spoken_ipa"]:
        st.write(f"{result.get('pronunciation_label', 'IPA')} tu transcript: {result['spoken_ipa']}")

    if result["feedback_ok"]:
        st.info(result["feedback"])
    else:
        st.warning(result["feedback"])
