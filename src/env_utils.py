from pathlib import Path


def get_env_value(env_file: Path, key: str) -> str:
    if not env_file.exists():
        return ""

    with env_file.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            env_key, env_value = line.split("=", 1)
            if env_key.strip() == key:
                return env_value.strip().strip('"').strip("'")

    return ""
