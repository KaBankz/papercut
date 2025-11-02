"""
Console receipt preview.
Formats tickets as ASCII receipts for console logging.
"""

from papercut.core.models import Ticket
from config import (
    config,
    RECEIPT_WIDTH,
    RECEIPT_PADDING,
    RECEIPT_INNER_WIDTH,
)


def _print_border_line(width: int = None, style: str = "top") -> None:
    """Print a border line for the receipt."""
    if width is None:
        width = RECEIPT_WIDTH
    if style == "top":
        print("┌" + "─" * width + "┐")
    elif style == "bottom":
        print("└" + "─" * width + "┘")


def _print_line(content: str, width: int = None) -> None:
    """Print a line with borders on both sides."""
    if width is None:
        width = RECEIPT_WIDTH
    if len(content) < width:
        content = content + " " * (width - len(content))
    elif len(content) > width:
        content = content[:width]
    print("│" + content + "│")


def _wrap_text(text: str, max_width: int) -> list[str]:
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


def _wrap_two_column(
    label: str, value: str, width: int = None, padding: int = None
) -> None:
    """Print text in two-column format with wrapping."""
    if width is None:
        width = RECEIPT_WIDTH
    if padding is None:
        padding = RECEIPT_PADDING

    usable_width = width - (padding * 2)
    max_col_width = int(usable_width * 0.45)

    # Wrap right column (value) if needed
    value_lines = []
    current_value = value
    while len(current_value) > max_col_width:
        split_at = max(
            current_value[:max_col_width].rfind(" "),
            current_value[:max_col_width].rfind(",") + 1,
        )
        if split_at <= 0:
            split_at = max_col_width
        value_lines.append(current_value[:split_at].rstrip())
        current_value = current_value[split_at:].lstrip()
    if current_value:
        value_lines.append(current_value)

    # Print first line: label left-aligned, value right-aligned
    if value_lines:
        gap = usable_width - len(label) - len(value_lines[0])
        content = " " * padding + label + " " * gap + value_lines[0] + " " * padding
        _print_line(content, width)

    # Print remaining value lines
    for value_line in value_lines[1:]:
        gap = usable_width - len(value_line)
        content = " " * padding + " " * gap + value_line + " " * padding
        _print_line(content, width)


def print_console_preview(ticket: Ticket) -> None:
    """
    Print a console preview of the ticket receipt.
    Uses ASCII borders to mimic receipt printer output.

    Args:
        ticket: Platform-agnostic ticket to display
    """
    width = RECEIPT_WIDTH
    padding = RECEIPT_PADDING
    inner_width = RECEIPT_INNER_WIDTH

    print("\n")
    _print_border_line(width, "top")
    _print_line("", width)

    # Company header
    if config.header.company_name is not None:
        _print_line(
            " " * padding
            + config.header.company_name.center(inner_width)
            + " " * padding,
            width,
        )

    # Company address
    if config.header.address_line1 is not None:
        _print_line(
            " " * padding
            + config.header.address_line1.center(inner_width)
            + " " * padding,
            width,
        )
    if config.header.address_line2 is not None:
        _print_line(
            " " * padding
            + config.header.address_line2.center(inner_width)
            + " " * padding,
            width,
        )

    if config.header.phone is not None:
        _print_line(
            " " * padding
            + f"Tel: {config.header.phone}".center(inner_width)
            + " " * padding,
            width,
        )

    if config.header.url is not None:
        _print_line(
            " " * padding + config.header.url.center(inner_width) + " " * padding, width
        )

    _print_line("", width)

    # Timestamp
    created_at = ticket.created_at.strftime("%b %d, %Y at %I:%M %p").center(inner_width)
    _print_line(" " * padding + created_at + " " * padding, width)
    _print_line("", width)

    # Details in two-column format
    _wrap_two_column("ID", ticket.identifier, width)
    _wrap_two_column("Team", ticket.team, width)
    _wrap_two_column("Priority", ticket.priority, width)
    _wrap_two_column("Status", ticket.status, width)

    if ticket.assignee:
        _wrap_two_column("Assignee", ticket.assignee, width)

    if ticket.due_date:
        due = ticket.due_date.strftime("%b %d, %Y")
        _wrap_two_column("Due", due, width)

    _wrap_two_column("Creator", ticket.created_by, width)

    if ticket.labels:
        label_names = ", ".join(ticket.labels)
        _wrap_two_column("Labels", label_names, width)

    _print_line("", width)

    # Ticket title (wrapped)
    title = ticket.title.strip()
    if len(title) > 350:
        title = title[:347] + "..."
    title_lines = _wrap_text(title, inner_width)
    for line in title_lines:
        _print_line(" " * padding + line + " " * padding, width)
    _print_line("", width)

    # Ticket description (wrapped)
    if ticket.description:
        desc = ticket.description.strip()
        if len(desc) > 350:
            desc = desc[:347] + "..."
        desc_lines = _wrap_text(desc, inner_width)
        for line in desc_lines:
            _print_line(" " * padding + line + " " * padding, width)
        _print_line("", width)

    # Footer section
    if not config.footer.disabled:
        if config.footer.qr_code_title is not None:
            _print_line(config.footer.qr_code_title.center(inner_width), width)
            _print_line("", width)

        if not config.footer.qr_code_disabled:
            _print_line("QR CODE HERE".center(inner_width), width)
            _print_line("", width)

        if config.footer.footer_text is not None:
            _print_line(
                " " * padding
                + config.footer.footer_text.center(inner_width)
                + " " * padding,
                width,
            )
            _print_line("", width)

    _print_border_line(width, "bottom")
    print()
