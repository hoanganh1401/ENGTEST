from pathlib import Path
import re
import unicodedata

from src.mongo_utils import get_learning_sets_collection, infer_set_type


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
    existing_options = get_quiz_file_options(data_dir)
    return _create_file_option(
        data_dir / "trac_nghiem",
        display_name,
        existing_names=set(existing_options.keys()),
        existing_file_names={path.name for path in existing_options.values()},
    )


def create_vocabulary_file_option(data_dir: Path, display_name: str) -> Path:
    existing_options = get_vocabulary_file_options(data_dir)
    return _create_file_option(
        data_dir / "tu_vung",
        display_name,
        existing_names=set(existing_options.keys()),
        existing_file_names={path.name for path in existing_options.values()},
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
    existing_file_names: set[str] | None = None,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    cleaned_name = " ".join(display_name.strip().split())
    if not cleaned_name:
        raise ValueError("Ten khong duoc de trong.")

    if cleaned_name in (existing_names or set()):
        raise ValueError("Ten nay da ton tai.")

    file_name = _build_unique_file_name(
        target_dir,
        cleaned_name,
        existing_file_names or set(),
    )
    metadata = _load_custom_metadata(target_dir)
    metadata[cleaned_name] = file_name
    _save_custom_metadata(target_dir, metadata)
    return target_dir / file_name


def _load_custom_metadata(target_dir: Path) -> dict[str, str]:
    set_type = infer_set_type(str(target_dir / "_placeholder.jsonl"))
    if set_type == "unknown":
        return {}

    try:
        collection = get_learning_sets_collection()
        documents = collection.find(
            {"set_type": set_type},
            {"_id": 0, "display_name": 1, "file_name": 1},
        ).sort("display_name", 1)
    except Exception:
        return {}

    return {
        str(document.get("display_name")): str(document.get("file_name"))
        for document in documents
        if document.get("display_name") and document.get("file_name")
    }


def _save_custom_metadata(target_dir: Path, metadata: dict[str, str]) -> None:
    set_type = infer_set_type(str(target_dir / "_placeholder.jsonl"))
    if set_type == "unknown":
        return

    collection = get_learning_sets_collection()
    for display_name, file_name in metadata.items():
        collection.update_one(
            {
                "set_type": set_type,
                "display_name": display_name,
            },
            {
                "$set": {
                    "set_type": set_type,
                    "display_name": display_name,
                    "file_name": file_name,
                }
            },
            upsert=True,
        )


def _build_unique_file_name(
    target_dir: Path,
    display_name: str,
    existing_file_names: set[str],
) -> str:
    base_name = _slugify(display_name) or "bo_moi"
    file_name = f"{base_name}.jsonl"
    counter = 2

    while (target_dir / file_name).exists() or file_name in existing_file_names:
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
