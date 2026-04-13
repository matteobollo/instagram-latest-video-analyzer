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
    # Create the directory and all its parents if they do not exist
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_handle(handle: str) -> str:
    """
    Sanitize an Instagram handle by stripping any leading/trailing whitespace and '@' characters,
    and ensuring that it only contains alphanumeric characters, underscores and periods.

    Args:
        handle: The Instagram handle to sanitize.

    Returns:
        The sanitized Instagram handle.

    Raises:
        ValueError: If the sanitized handle does not match the regular expression
            '[A-Za-z0-9._]+'
    """
    clean = handle.strip().lstrip('@').strip()
    # Ensure that the handle only contains alphanumeric characters, underscores and periods
    if not re.fullmatch(r'[A-Za-z0-9._]+', clean):
        raise ValueError('Instagram handle non valido')
