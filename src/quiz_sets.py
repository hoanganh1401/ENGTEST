from pathlib import Path
import json
import re
import unicodedata


QUIZ_FILES = {
    "Kiem tra V-ing / To V": "questions.jsonl",
    "Kiem tra word choice": "word_choice.jsonl",
    "Kiem tra tu loai": "word_forms.jsonl",
    "Kiem tra thi": "tenses.jsonl",
    "Kiem tra cum dong tu": "phrasal_verbs.jsonl",
    "Tieng Nhat co ban": "japanese_basic.jsonl",
    "Tieng Han co ban": "korean_basic.jsonl",
}


VOCABULARY_FILES = {
    "Tu vung tieng Anh co ban": "english_basic.jsonl",
    "Tu vung tieng Anh nang cao": "english_advanced.jsonl",
    "Tu vung tieng Nhat co ban": "japanese_basic.jsonl",
    "Tu vung tieng Han co ban": "korean_basic.jsonl",
    "Tu vung tieng Trung HSK1": "tuvunghsk1.jsonl",
}


def get_quiz_file_options(data_dir: Path) -> dict[str, Path]:
    options = {
        quiz_name: data_dir / "trac_nghiem" / file_name
        for quiz_name, file_name in QUIZ_FILES.items()
    }
    return _with_custom_file_options(options, data_dir / "trac_nghiem")


def get_vocabulary_file_options(data_dir: Path) -> dict[str, Path]:
    options = {
        vocabulary_name: data_dir / "tu_vung" / file_name
        for vocabulary_name, file_name in VOCABULARY_FILES.items()
    }
    return _with_custom_file_options(options, data_dir / "tu_vung")


def create_quiz_file_option(data_dir: Path, display_name: str) -> Path:
    return _create_file_option(
        data_dir / "trac_nghiem",
        display_name,
        existing_names=set(get_quiz_file_options(data_dir).keys()),
    )


def create_vocabulary_file_option(data_dir: Path, display_name: str) -> Path:
    return _create_file_option(
        data_dir / "tu_vung",
        display_name,
        existing_names=set(get_vocabulary_file_options(data_dir).keys()),
    )


def _with_custom_file_options(options: dict[str, Path], target_dir: Path) -> dict[str, Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    merged_options = options.copy()

    for display_name, file_name in _load_custom_metadata(target_dir).items():
        if display_name.strip() and file_name.strip():
            _add_option(merged_options, display_name.strip(), target_dir / file_name.strip())

    known_files = {path.name for path in merged_options.values()}
    for file_path in sorted(target_dir.glob("*.jsonl")):
        if file_path.name in known_files:
            continue

        _add_option(merged_options, _display_name_from_file(file_path), file_path)

    return merged_options


def _create_file_option(
    target_dir: Path,
    display_name: str,
    existing_names: set[str] | None = None,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    cleaned_name = " ".join(display_name.strip().split())
    if not cleaned_name:
        raise ValueError("Ten khong duoc de trong.")

    if cleaned_name in (existing_names or set()):
        raise ValueError("Ten nay da ton tai.")

    file_name = _build_unique_file_name(target_dir, cleaned_name)
    metadata = _load_custom_metadata(target_dir)
    metadata[cleaned_name] = file_name
    _save_custom_metadata(target_dir, metadata)
    return target_dir / file_name


def _metadata_path(target_dir: Path) -> Path:
    return target_dir / "_sets.json"


def _load_custom_metadata(target_dir: Path) -> dict[str, str]:
    path = _metadata_path(target_dir)
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            metadata = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(metadata, dict):
        return {}

    return {
        str(display_name): str(file_name)
        for display_name, file_name in metadata.items()
    }


def _save_custom_metadata(target_dir: Path, metadata: dict[str, str]) -> None:
    path = _metadata_path(target_dir)
    with path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)


def _build_unique_file_name(target_dir: Path, display_name: str) -> str:
    base_name = _slugify(display_name) or "bo_moi"
    file_name = f"{base_name}.jsonl"
    counter = 2

    while (target_dir / file_name).exists():
        file_name = f"{base_name}_{counter}.jsonl"
        counter += 1

    return file_name


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    ascii_value = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )
    ascii_value = ascii_value.replace("đ", "d").replace("Đ", "D")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value.lower()).strip("_")
    return slug


def _display_name_from_file(file_path: Path) -> str:
    return file_path.stem.replace("_", " ").strip().title()


def _add_option(options: dict[str, Path], display_name: str, file_path: Path) -> None:
    option_name = display_name
    counter = 2
    while option_name in options:
        if options[option_name] == file_path:
            return

        option_name = f"{display_name} ({counter})"
        counter += 1

    options[option_name] = file_path
