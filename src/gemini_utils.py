import json
import unicodedata
import urllib.error
import urllib.request


GEMINI_MODEL = "gemini-2.5-flash"
EXPLANATION_PROMPT_VERSION = "v3"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def explain_wrong_answer(
    api_key: str,
    question: str,
    options: dict,
    user_answer: str,
    correct_answer: str,
) -> tuple[bool, str]:
    if not api_key:
        return False, "Chua cau hinh GEMINI_API_KEY."

    prompt = _build_explanation_prompt(
        question=question,
        options=options,
        user_answer=user_answer,
        correct_answer=correct_answer,
    )
    ok, explanation = _request_explanation(api_key, prompt)
    if not ok:
        return False, explanation

    if _is_useful_explanation(explanation):
        return True, explanation

    retry_prompt = _build_retry_prompt(prompt, explanation)
    ok, retry_explanation = _request_explanation(api_key, retry_prompt)
    if not ok:
        return False, retry_explanation

    if _is_useful_explanation(retry_explanation):
        return True, retry_explanation

    return True, (
        retry_explanation
        + "\n\nLuu y: Gemini tra ve giai thich hoi ngan. "
        "Ban co the bam lai nut AI de tao lai cau giai thich."
    )


def _request_explanation(api_key: str, prompt: str) -> tuple[bool, str]:
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
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    request = urllib.request.Request(
        GEMINI_ENDPOINT,
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

    explanation = _extract_text(response_data)
    if not explanation:
        return False, "Gemini khong tra ve noi dung giai thich."

    return True, explanation


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
