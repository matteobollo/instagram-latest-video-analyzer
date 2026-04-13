from pathlib import Path
import re


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_handle(handle: str) -> str:
    clean = handle.strip().lstrip('@').strip()
    if not re.fullmatch(r'[A-Za-z0-9._]+', clean):
        raise ValueError('Instagram handle non valido')
    return clean
