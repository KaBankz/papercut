"""
Shared utility functions for the core package.
Common text processing and formatting utilities.
"""

from typing import Optional
from datetime import datetime, timezone


def utc_to_local(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to local system timezone.

    Args:
        utc_dt: UTC datetime object (may or may not be timezone-aware)

    Returns:
        Datetime object in the local system timezone
    """
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)

    # Convert to local timezone
    return utc_dt.astimezone()


def normalize_optional_string(value: str | None) -> Optional[str]:
    """
    Convert empty strings to None for opt-out behavior.

    Args:
        value: String value from config or input

    Returns:
        None if value is empty string, otherwise the value as-is
    """
    if value == "":
        return None
    return value


def wrap_text(text: str, max_width: int) -> list[str]:
    """
    Wrap text to fit within a maximum width, breaking at word boundaries.

    Args:
        text: The text to wrap
        max_width: Maximum width per line

    Returns:
        List of wrapped lines
    """
    if len(text) <= max_width:
        return [text]

    lines = []
    words = text.split()
    current_line = []
    current_length = 0

    for word in words:
        word_len = len(word) + (1 if current_line else 0)  # +1 for space between words
        if current_length + word_len <= max_width:
            current_line.append(word)
            current_length += word_len
        else:
            if current_line:
                lines.append(" ".join(current_line))
            # If single word is too long, force break it
            if len(word) > max_width:
                lines.append(word[:max_width])
                current_line = []
                current_length = 0
            else:
                current_line = [word]
                current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length including ellipsis

    Returns:
        Truncated text with '...' if exceeds max_length
    """
    text = text.strip()
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
