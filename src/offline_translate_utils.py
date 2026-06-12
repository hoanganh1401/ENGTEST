from pathlib import Path
import os
import shutil
import tempfile


ARGOS_PACKAGES_DIR = Path(__file__).resolve().parents[1] / "model_argostranslate"


def configure_argos_packages_dir() -> Path:
    ARGOS_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_argos_packages(ARGOS_PACKAGES_DIR)
    os.environ["ARGOS_PACKAGES_DIR"] = str(ARGOS_PACKAGES_DIR)
    return ARGOS_PACKAGES_DIR


def _migrate_legacy_argos_packages(target_dir: Path) -> None:
    legacy_dir = Path.home() / ".local" / "share" / "argos-translate" / "packages"
    if not legacy_dir.exists() or legacy_dir.resolve() == target_dir.resolve():
        return

    for item in legacy_dir.iterdir():
        target_path = target_dir / item.name
        if target_path.exists():
            continue

        if item.is_dir():
            shutil.copytree(item, target_path)
        else:
            shutil.copy2(item, target_path)


def get_installed_languages() -> tuple[bool, list]:
    configure_argos_packages_dir()
    try:
        import argostranslate.translate
        import argostranslate.settings
    except ImportError:
        return False, []

    try:
        argostranslate.settings.package_data_dir = ARGOS_PACKAGES_DIR
        argostranslate.settings.package_dirs = [ARGOS_PACKAGES_DIR]
        return True, argostranslate.translate.get_installed_languages()
    except Exception:
        return True, []


def get_language_options() -> dict[str, object]:
    ok, languages = get_installed_languages()
    if not ok:
        return {}

    return {
        f"{language.name} ({language.code})": language
        for language in sorted(languages, key=lambda item: item.name.lower())
    }


def get_target_language_options(from_language) -> dict[str, object]:
    translations = from_language.translations_from
    return {
        f"{translation.to_lang.name} ({translation.to_lang.code})": translation.to_lang
        for translation in sorted(
            translations,
            key=lambda item: item.to_lang.name.lower(),
        )
    }


def translate_text(text: str, from_language, to_language) -> tuple[bool, str]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return False, "Hay nhap van ban can dich."

    translation = from_language.get_translation(to_language)
    if translation is None:
        return False, "Chua cai goi dich cho cap ngon ngu nay."

    try:
        return True, translation.translate(cleaned_text)
    except Exception as error:
        return False, f"Khong dich duoc van ban: {error}"


def install_argos_model(uploaded_file) -> tuple[bool, str]:
    configure_argos_packages_dir()
    if uploaded_file is None:
        return False, "Hay chon file .argosmodel."

    file_name = uploaded_file.name or ""
    if not file_name.lower().endswith(".argosmodel"):
        return False, "File ngon ngu phai co duoi .argosmodel."

    try:
        import argostranslate.package
        import argostranslate.settings
    except ImportError:
        return False, "Chua cai thu vien argostranslate. Hay chay: pip install -r requirements.txt"

    argostranslate.settings.package_data_dir = ARGOS_PACKAGES_DIR
    argostranslate.settings.package_dirs = [ARGOS_PACKAGES_DIR]

    suffix = Path(file_name).suffix or ".argosmodel"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_path = Path(temp_file.name)

        argostranslate.package.install_from_path(str(temp_path))
    except Exception as error:
        return False, f"Khong cai duoc goi ngon ngu: {error}"

    return True, f"Da cai goi ngon ngu tu {file_name} vao {ARGOS_PACKAGES_DIR}."
