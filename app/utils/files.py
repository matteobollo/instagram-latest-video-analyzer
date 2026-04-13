from pathlib import Path
import re


def ensure_dir(path: str | Path) -> Path:
    """
    Ensure that a directory exists, creating it if it does not.

    Args:
        path: The path to the directory to ensure.

    Returns:
        The Path object of the ensured directory.
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_handle(handle: str) -> str:
    """
    Sanitize an Instagram handle by stripping leading/trailing whitespace and '@',
    and ensuring that it only contains alphanumeric characters, underscores and periods.
    """
    clean = handle.strip().lstrip('@').strip()

    if not clean:
        raise ValueError('Instagram handle non valido')

    if not re.fullmatch(r'[A-Za-z0-9._]+', clean):
        raise ValueError('Instagram handle non valido')

    return clean