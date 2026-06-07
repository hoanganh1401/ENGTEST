import json
import re
import unicodedata
import urllib.error
import urllib.request


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_VOCABULARY_MODEL = "gemini-2.5-flash-lite"
EXPLANATION_PROMPT_VERSION = "v3"
VOCABULARY_PRONUNCIATION_PROMPT_VERSION = "v3"
GEMINI_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)


def explain_wrong_answer(
    api_key: str,
    question: str,
    options: dict,
    user_answer: str,
    correct_answer: str,
    model: str = "",
) -> tuple[bool, str]:
    if not api_key:
        return False, "Chua cau hinh GEMINI_API_KEY."

    prompt = _build_explanation_prompt(
        question=question,
        options=options,
        user_answer=user_answer,
        correct_answer=correct_answer,
    )
    ok, explanation = _request_explanation(api_key, prompt, model)
    if not ok:
        return False, explanation

    if _is_useful_explanation(explanation):
        return True, explanation

    retry_prompt = _build_retry_prompt(prompt, explanation)
    ok, retry_explanation = _request_explanation(api_key, retry_prompt, model)
    if not ok:
        return False, retry_explanation

    if _is_useful_explanation(retry_explanation):
        return True, retry_explanation

    return True, (
        retry_explanation
        + "\n\nLuu y: Gemini tra ve giai thich hoi ngan. "
        "Ban co the bam lai nut AI de tao lai cau giai thich."
    )


def get_vocabulary_pronunciation(
    api_key: str,
    word: str,
    language: str = "",
    model: str = "",
) -> tuple[bool, str]:
    if not api_key:
        return False, "Chua cau hinh GEMINI_VOCABULARY_API_KEY."

    cleaned_word = word.strip()
    if not cleaned_word:
        return False, "Khong co tu vung de tao phien am."

    prompt = _build_vocabulary_pronunciation_prompt(
        word=cleaned_word,
        language=language.strip(),
    )
    ok, pronunciation = _request_gemini_content(
        api_key=api_key,
        prompt=prompt,
        temperature=0.1,
        max_output_tokens=256,
        empty_message="Gemini khong tra ve phien am.",
        model=model or DEFAULT_VOCABULARY_MODEL,
    )
    if not ok:
        return False, pronunciation

    return True, _format_vocabulary_pronunciation(pronunciation, language)


def _request_explanation(api_key: str, prompt: str, model: str = "") -> tuple[bool, str]:
    return _request_gemini_content(
        api_key=api_key,
        prompt=prompt,
        temperature=0.2,
        max_output_tokens=1024,
        empty_message="Gemini khong tra ve noi dung giai thich.",
        model=model or DEFAULT_GEMINI_MODEL,
    )


def _request_gemini_content(
    api_key: str,
    prompt: str,
    temperature: float,
    max_output_tokens: int,
    empty_message: str,
    model: str,
) -> tuple[bool, str]:
    cleaned_model = _normalize_gemini_model(model)
    if not cleaned_model:
        return False, "Chua cau hinh model Gemini hop le."

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }

    request = urllib.request.Request(
        GEMINI_ENDPOINT_TEMPLATE.format(model=cleaned_model),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        return False, f"Gemini API loi {error.code}: {error_body}"
    except urllib.error.URLError as error:
        return False, f"Khong the ket noi Gemini API: {error.reason}"
    except TimeoutError:
        return False, "Gemini API phan hoi qua lau."

    content = _extract_text(response_data)
    if not content:
        return False, empty_message

    return True, content


def _build_explanation_prompt(
    question: str,
    options: dict,
    user_answer: str,
    correct_answer: str,
) -> str:
    option_lines = "\n".join(
        f"{key}. {value}" for key, value in options.items()
    )
    user_answer_text = options.get(user_answer, "Chua chon dap an")
    correct_answer_text = options.get(correct_answer, "")

    return f"""
Nhiem vu: giai thich dap an sai cho mot cau trac nghiem tieng Anh.
Nguoi hoc la nguoi Viet. Chi tra loi bang tieng Viet.
Khong chao hoi. Khong viet cau mo dau xa giao.
Phai giai thich truc tiep vao cau hoi.

Cau hoi:
{question}

Lua chon:
{option_lines}

Hoc sinh chon: {user_answer}. {user_answer_text}
Dap an dung: {correct_answer}. {correct_answer_text}

Hay tra loi dung cau truc sau, khong bo muc nao:

**Dap an ban chon:** {user_answer}. {user_answer_text}

**Dap an dung:** {correct_answer}. {correct_answer_text}

**Quy tac can nho:** Neu quy tac ngu phap/tu vung lien quan den cau hoi nay.

**Vi sao dap an ban chon sai:** Giai thich cu the vi sao "{user_answer_text}" khong phu hop trong cau nay.

**Vi sao dap an dung dung:** Giai thich cu the vi sao "{correct_answer_text}" phu hop trong cau nay.

**Vi du tuong tu:** Dua 1 cau vi du ngan va dap an dung.

Yeu cau:
- Phai nhac lai noi dung cua dap an sai va dap an dung.
- Khong noi chung chung nhu "vi xong khong con gi khac".
- Neu khong du thong tin, hay noi ro thieu thong tin nao.
- Toi thieu 80 tu, toi da 220 tu.
""".strip()


def _normalize_gemini_model(model: str) -> str:
    cleaned_model = model.strip()
    if cleaned_model.startswith("models/"):
        cleaned_model = cleaned_model.removeprefix("models/")

    if not cleaned_model or any(character.isspace() for character in cleaned_model):
        return ""

    return cleaned_model


def _build_vocabulary_pronunciation_prompt(word: str, language: str = "") -> str:
    if "trung" in language.lower():
        return f"""
Nhiem vu: tao pinyin cho tu/cum tu tieng Trung.
Nguoi hoc la nguoi Viet. Chi tra loi bang tieng Viet.
Khong chao hoi. Khong giai thich dai dong.

Tu/cum tu tieng Trung:
{word}

Hay tra loi dung mot dong theo cau truc sau:
Pinyin: pinyin co dau thanh

Yeu cau:
- Chi viet pinyin cua chinh tu/cum tu tren.
- Bat buoc dung dau thanh.
- Khong them muc "Tu", "Ngon ngu", "Phien am" hay bat ky noi dung nao khac.
""".strip()

    if "anh" in language.lower():
        return f"""
Nhiem vu: tao phien am IPA cho tu/cum tu tieng Anh.
Nguoi hoc la nguoi Viet. Chi tra loi bang tieng Viet.
Khong chao hoi. Khong giai thich dai dong.

Tu/cum tu tieng Anh:
{word}

Hay tra loi dung mot dong theo cau truc sau:
Phien am IPA: /.../

Yeu cau:
- Chi viet phien am IPA cua chinh tu/cum tu tren.
- Uu tien IPA Anh-My thong dung.
- Khong them muc "Tu", "Ngon ngu", "Pinyin" hay bat ky noi dung nao khac.
""".strip()

    return f"""
Nhiem vu: tao phien am cho tu/cum tu vung.
Nguoi hoc la nguoi Viet. Chi tra loi bang tieng Viet.
Khong chao hoi. Khong viet cau mo dau xa giao.

Tu/cum tu:
{word}

Hay tra loi ngan gon dung cau truc sau:

**Tu:** {word}
**Ngon ngu:** ten ngon ngu ban nhan dien duoc
**Phien am:** phien am IPA neu phu hop; neu khong co IPA thong dung, ghi cach doc gan dung
**Pinyin:** neu la tieng Trung thi ghi pinyin co dau thanh; neu khong phai tieng Trung thi ghi "Khong ap dung"

Yeu cau:
- Neu la tieng Trung, bat buoc co pinyin co dau thanh.
- Neu la tieng Anh, uu tien IPA Anh-My hoac IPA thong dung.
- Khong giai thich dai dong.
- Toi da 80 tu.
""".strip()


def _extract_text(response_data: dict) -> str:
    candidates = response_data.get("candidates", [])
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(
        part.get("text", "")
        for part in parts
        if part.get("text")
    ).strip()


def _format_vocabulary_pronunciation(pronunciation: str, language: str) -> str:
    cleaned = " ".join(pronunciation.replace("\n", " ").split())
    normalized_language = _remove_vietnamese_marks(language.lower())

    if "trung" in normalized_language:
        pinyin = _extract_pronunciation_field(cleaned, ["Pinyin"])
        return f"Pinyin: {pinyin}" if pinyin else cleaned

    if "anh" in normalized_language:
        ipa = _extract_pronunciation_field(
            cleaned,
            ["Phien am IPA", "Phien am", "IPA"],
        )
        return f"Phien am IPA: {ipa}" if ipa else cleaned

    return cleaned


def _extract_pronunciation_field(text: str, labels: list[str]) -> str:
    for label in labels:
        pattern = (
            rf"(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*:\s*"
            r"(.+?)(?=\s*(?:\*\*)?(?:Tu|Ngon ngu|Phien am IPA|Phien am|IPA|Pinyin)"
            r"(?:\*\*)?\s*:|$)"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" *")

    return ""


def _is_useful_explanation(explanation: str) -> bool:
    normalized_explanation = _remove_vietnamese_marks(explanation.strip().lower())
    return (
        len(normalized_explanation) >= 100
        and "dap an dung" in normalized_explanation
        and ("vi sao" in normalized_explanation or "quy tac" in normalized_explanation)
    )


def _remove_vietnamese_marks(value: str) -> str:
    value = value.replace("đ", "d")
    normalized = unicodedata.normalize("NFD", value)
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )


def _build_retry_prompt(original_prompt: str, short_explanation: str) -> str:
    return f"""
Lan tra loi truoc cua ban qua ngan va khong dat yeu cau:
{short_explanation}

Hay tra loi lai. Khong chao hoi. Khong viet cau mo dau.
Bat buoc giai thich day du theo tung muc.

{original_prompt}
""".strip()
