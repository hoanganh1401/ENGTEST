from pathlib import Path
import tempfile


PHONEMIZER_LANGUAGE_BY_NAME = {
    "tieng Anh": "en-us",
}


def transcribe_audio_file(
    model,
    audio_path: Path,
    language: str = "",
) -> tuple[bool, str]:
    try:
        transcribe_kwargs = {"beam_size": 5}
        if language:
            transcribe_kwargs["language"] = language

        segments, _info = model.transcribe(str(audio_path), **transcribe_kwargs)
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as error:
        return False, f"Whisper khong xu ly duoc audio: {error}"

    if not transcript:
        return False, "Whisper khong nghe duoc noi dung nao. Hay thu am lai ro hon."

    return True, transcript


def write_uploaded_audio(uploaded_audio) -> Path:
    suffix = Path(uploaded_audio.name or "speaking_audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_audio.getbuffer())
        return Path(temp_file.name)


def get_phonemizer_language(language_name: str) -> str:
    return PHONEMIZER_LANGUAGE_BY_NAME.get(language_name, "en-us")


def get_pronunciation_system(language_name: str) -> str:
    if "trung" in language_name.lower():
        return "pinyin"
    return "ipa"


def text_to_pinyin(text: str) -> tuple[bool, str]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return False, "Khong co text de tao pinyin."

    try:
        from pypinyin import Style, lazy_pinyin
    except ImportError:
        return False, "Chua cai thu vien pypinyin. Hay chay: pip install -r requirements.txt"

    try:
        pinyin = lazy_pinyin(cleaned_text, style=Style.TONE3, errors="ignore")
    except Exception as error:
        return False, f"Khong tao duoc pinyin: {error}"

    pinyin_text = " ".join(
        _convert_numbered_pinyin_to_marks(item)
        for item in pinyin
        if item.strip()
    )
    if not pinyin_text:
        return False, "Khong tim thay chu Han de tao pinyin."

    return True, pinyin_text


def _convert_numbered_pinyin_to_marks(value: str) -> str:
    tone = value[-1] if value and value[-1].isdigit() else ""
    syllable = value[:-1] if tone else value
    if tone in ("", "5", "0"):
        return syllable.replace("v", "ü")

    marked_vowels = {
        "a": "āáǎà",
        "e": "ēéěè",
        "i": "īíǐì",
        "o": "ōóǒò",
        "u": "ūúǔù",
        "ü": "ǖǘǚǜ",
    }
    normalized = syllable.replace("u:", "ü").replace("v", "ü")
    tone_index = int(tone) - 1
    target_index = _get_pinyin_tone_vowel_index(normalized)
    if target_index == -1:
        return normalized

    vowel = normalized[target_index]
    marked_vowel = marked_vowels.get(vowel, vowel)[tone_index]
    return normalized[:target_index] + marked_vowel + normalized[target_index + 1 :]


def _get_pinyin_tone_vowel_index(syllable: str) -> int:
    for vowel in ("a", "e"):
        index = syllable.find(vowel)
        if index != -1:
            return index

    ou_index = syllable.find("ou")
    if ou_index != -1:
        return ou_index

    for index in range(len(syllable) - 1, -1, -1):
        if syllable[index] in "ioüu":
            return index

    return -1


def phonemize_to_ipa(
    text: str,
    language: str = "en-us",
    espeak_library_path: str = "",
) -> tuple[bool, str]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return False, "Khong co text de tao IPA."

    try:
        from phonemizer import phonemize
    except ImportError:
        return False, "Chua cai thu vien phonemizer. Hay chay: pip install -r requirements.txt"

    try:
        if espeak_library_path:
            from phonemizer.backend.espeak.wrapper import EspeakWrapper

            EspeakWrapper.set_library(espeak_library_path)

        ipa = phonemize(
            cleaned_text,
            language=language,
            backend="espeak",
            strip=True,
            preserve_punctuation=True,
            with_stress=True,
            njobs=1,
        )
    except Exception as error:
        return False, (
            "Phonemizer khong tao duoc IPA. Thu vien nay can backend espeak. "
            f"Chi tiet loi: {error}"
        )

    return True, " ".join(ipa.split())
