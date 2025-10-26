"""
Console receipt preview.
Formats tickets as ASCII receipts for console logging.
"""

from papercut.core.models import Ticket
from config import (
    COMPANY_NAME,
    COMPANY_ADDRESS_LINE1,
    COMPANY_ADDRESS_LINE2,
    COMPANY_ADDRESS_LINE3,
    COMPANY_URL,
    COMPANY_PHONE,
    COMPANY_TAGLINE,
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
    if COMPANY_NAME:
        _print_line(
            " " * padding + COMPANY_NAME.center(inner_width) + " " * padding, width
        )
        _print_line("", width)

    # Company address
    if COMPANY_ADDRESS_LINE1:
        _print_line(
            " " * padding + COMPANY_ADDRESS_LINE1.center(inner_width) + " " * padding,
            width,
        )
    if COMPANY_ADDRESS_LINE2:
        _print_line(
            " " * padding + COMPANY_ADDRESS_LINE2.center(inner_width) + " " * padding,
            width,
        )
    if COMPANY_ADDRESS_LINE3:
        _print_line(
            " " * padding + COMPANY_ADDRESS_LINE3.center(inner_width) + " " * padding,
            width,
        )

    if COMPANY_PHONE:
        _print_line(
            " " * padding + f"Tel: {COMPANY_PHONE}".center(inner_width) + " " * padding,
            width,
        )

    if COMPANY_URL:
        _print_line(
            " " * padding + COMPANY_URL.center(inner_width) + " " * padding, width
        )

    _print_line("", width)

    # Timestamp
    created_at = ticket.created_at.strftime("%b %d, %Y at %I:%M %p")
    _print_line(" " * padding + created_at + " " * padding, width)
    _print_line("", width)

    # Details in two-column format
    _wrap_two_column("Team", ticket.team, width)
    _wrap_two_column("Priority", ticket.priority, width)
    _wrap_two_column("Status", ticket.status, width)

    if ticket.assignee:
        _wrap_two_column("Assignee", ticket.assignee, width)

    if ticket.due_date:
        due = ticket.due_date.strftime("%b %d, %Y")
        _wrap_two_column("Due", due, width)

    if ticket.labels:
        label_names = ", ".join(ticket.labels)
        _wrap_two_column("Labels", label_names, width)

    _wrap_two_column("Created by", ticket.created_by, width)
    _wrap_two_column("ID", ticket.identifier, width)
    _print_line("", width)

    # Separator
    _print_line(" " * padding + "─" * inner_width + " " * padding, width)
    _print_line("", width)

    # Ticket title
    _print_line(" " * padding + ticket.title.upper() + " " * padding, width)
    _print_line("", width)

    # Ticket description
    if ticket.description:
        desc = ticket.description.replace("\n", " ").strip()
        _print_line(" " * padding + desc + " " * padding, width)
        _print_line("", width)

    # Separator
    _print_line(" " * padding + "─" * inner_width + " " * padding, width)
    _print_line("", width)

    # Footer tagline
    if COMPANY_TAGLINE:
        _print_line(
            " " * padding + COMPANY_TAGLINE.center(inner_width) + " " * padding,
            width,
        )
        _print_line("", width)

    _print_border_line(width, "bottom")
    print()
