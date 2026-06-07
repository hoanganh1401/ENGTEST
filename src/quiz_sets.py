from pathlib import Path


QUIZ_FILES = {
    "Kiem tra V-ing / To V": "questions.jsonl",
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
}


def get_quiz_file_options(data_dir: Path) -> dict[str, Path]:
    return {
        quiz_name: data_dir / "trac_nghiem" / file_name
        for quiz_name, file_name in QUIZ_FILES.items()
    }


def get_vocabulary_file_options(data_dir: Path) -> dict[str, Path]:
    return {
        vocabulary_name: data_dir / "tu_vung" / file_name
        for vocabulary_name, file_name in VOCABULARY_FILES.items()
    }
