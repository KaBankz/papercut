"""
Markdown renderer for receipt printers.
Converts markdown text to formatted receipt output using python-escpos.
"""

import logging
import re

logger = logging.getLogger(__name__)


def render_markdown_to_receipt(printer, markdown_text: str) -> None:
    """
    Render markdown text to receipt printer with basic formatting.

    Supports:
    - H1, H2, H3+ headers with styled rendering
    - Bullet lists with • prefix
    - Everything else prints as raw markdown (preserves all content)

    All text is left-aligned. No information is lost - unsupported
    markdown syntax prints exactly as-is.

    Args:
        printer: ESC/POS printer instance
        markdown_text: Markdown string to render
    """
    if not markdown_text or not markdown_text.strip():
        return

    lines = markdown_text.split("\n")
    columns = printer.profile.get_columns(font="a")

    for line in lines:
        # Detect headers (must be at line start)
        if line.startswith("# ") and not line.startswith("## "):
            _render_h1(printer, line[2:], columns)
        elif line.startswith("## ") and not line.startswith("### "):
            _render_h2(printer, line[3:], columns)
        elif line.startswith("### "):
            # H3, H4, H5, H6 all get same treatment
            header_text = line.lstrip("#").strip()
            _render_h3_plus(printer, header_text, columns)
        # Detect bullet lists (with space after marker)
        elif line.strip().startswith(("* ", "- ")) and len(line.strip()) > 2:
            _render_bullet(printer, line.strip()[2:], columns)
        # Blank lines
        elif line.strip() == "":
            printer.ln()
        # Everything else: raw markdown
        else:
            _render_text(printer, line, columns)


def _render_h1(printer, text: str, columns: int) -> None:
    """
    Render H1 header: double width + double height + bold.
    Left-aligned with spacing before/after.
    """
    printer.set(bold=True, double_width=True, double_height=True)
    # Half columns because double_width makes each char 2x wide
    printer.block_text(text, columns=columns // 2)
    printer.set_with_default()


def _render_h2(printer, text: str, columns: int) -> None:
    """
    Render H2 header: double height + bold.
    Left-aligned with spacing before.
    """
    printer.set(bold=True, double_height=True)
    printer.block_text(text, columns=columns)
    printer.set_with_default()


def _render_h3_plus(printer, text: str, columns: int) -> None:
    """
    Render H3+ headers (H3, H4, H5, H6): bold only.
    Left-aligned with spacing before.
    """
    printer.set(bold=True)
    printer.block_text(text, columns=columns)
    printer.set_with_default()


def _render_bullet(printer, text: str, columns: int) -> None:
    """
    Render bullet list item with • prefix.
    Text is auto-wrapped to fit receipt width.
    Supports inline formatting (bold/italic).
    """
    # Print bullet
    printer.text("• ")
    # Render text with inline formatting
    # Note: We don't adjust columns here since we're handling wrapping manually
    _render_text_with_inline_formatting(printer, text, columns - 2)
    printer.ln()


def _render_text_with_inline_formatting(printer, text: str, columns: int) -> None:
    """
    Render text with inline markdown formatting.

    Supported inline formats:
    - **bold** → bold text
    - *italic* → underline (escpos doesn't support italic)
    - `code` → prints as-is (no special formatting)

    Other markdown (links, images, etc.) prints as-is.
    """
    # Parse inline formatting and split into segments
    segments = _parse_inline_formatting(text)

    # Collect all text segments to use block_text for proper wrapping
    if all(seg["type"] == "normal" for seg in segments):
        # No formatting, use block_text for efficient wrapping
        printer.block_text(text, columns=columns)
    else:
        # Has formatting, need to print with styles
        for segment in segments:
            content = segment["content"]
            seg_type = segment["type"]

            if seg_type == "bold":
                printer.set(bold=True)
                printer.text(content)
                printer.set_with_default()
            elif seg_type == "italic":
                printer.set(underline=True)
                printer.text(content)
                printer.set_with_default()
            else:
                printer.text(content)


def _parse_inline_formatting(text: str) -> list:
    """
    Parse inline markdown formatting into segments.

    Returns list of dicts: [{'type': 'normal'|'bold'|'italic', 'content': 'text'}]

    Handles:
    - **bold**
    - *italic* (but not inside words)
    """
    segments = []
    current_pos = 0

    # Pattern matches **bold** and *italic* (with word boundaries for italic)
    # Bold: **text**
    # Italic: *text* (but not mid-word like *something* in the middle)
    pattern = r"(\*\*([^*]+?)\*\*)|(?<!\w)(\*([^*]+?)\*)(?!\w)"

    for match in re.finditer(pattern, text):
        # Add text before the match
        if match.start() > current_pos:
            segments.append(
                {"type": "normal", "content": text[current_pos : match.start()]}
            )

        # Add the formatted text
        if match.group(1):  # **bold**
            segments.append({"type": "bold", "content": match.group(2)})
        elif match.group(3):  # *italic*
            segments.append({"type": "italic", "content": match.group(4)})

        current_pos = match.end()

    # Add remaining text
    if current_pos < len(text):
        segments.append({"type": "normal", "content": text[current_pos:]})

    return segments if segments else [{"type": "normal", "content": text}]


def _render_text(printer, text: str, columns: int) -> None:
    """
    Render regular text with inline markdown formatting.

    Supports:
    - **bold** → bold text
    - *italic* → underline (escpos doesn't support italic)
    - Everything else prints as-is
    """
    if text.strip():
        _render_text_with_inline_formatting(printer, text, columns)
