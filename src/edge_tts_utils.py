import asyncio
import hashlib
import re
from pathlib import Path


VOICE_BY_LANGUAGE = {
    "tieng Anh": "en-US-JennyNeural",
    "tieng Trung": "zh-CN-XiaoxiaoNeural",
    "tieng Nhat": "ja-JP-NanamiNeural",
    "tieng Han": "ko-KR-SunHiNeural",
}


def get_tts_language(vocabulary_name: str) -> str:
    normalized_name = vocabulary_name.lower()
    if "tieng trung" in normalized_name:
        return "tieng Trung"
    if "tieng nhat" in normalized_name:
        return "tieng Nhat"
    if "tieng han" in normalized_name:
        return "tieng Han"
    if "tieng anh" in normalized_name:
        return "tieng Anh"
    return "tieng Anh"


def get_tts_voice(language: str) -> str:
    return VOICE_BY_LANGUAGE.get(language, VOICE_BY_LANGUAGE["tieng Anh"])


def get_audio_cache_path(cache_dir: Path, text: str, voice: str) -> Path:
    normalized_text = " ".join(text.strip().split())
    safe_voice = re.sub(r"[^A-Za-z0-9_-]+", "_", voice)
    digest = hashlib.sha256(f"{voice}:{normalized_text}".encode("utf-8")).hexdigest()
    return cache_dir / f"{safe_voice}_{digest[:16]}.mp3"


async def _save_edge_tts_audio(text: str, voice: str, output_path: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output_path))


def create_edge_tts_audio(text: str, voice: str, output_path: Path) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "Khong co tu de doc."

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        return True, str(output_path)

    try:
        asyncio.run(_save_edge_tts_audio(text.strip(), voice, output_path))
    except ImportError:
        return False, "Chua cai thu vien edge-tts. Hay chay: pip install -r requirements.txt"
    except Exception as error:
        return False, f"Khong tao duoc audio bang Edge TTS: {error}"

    return True, str(output_path)
