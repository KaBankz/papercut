"""
ASCII receipt printing functions.
Handles all the visual formatting and rendering of Linear tickets as ASCII receipts.
"""

from datetime import datetime
from models import LinearWebhook
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


def print_border_line(width: int = None, style: str = "top") -> None:
    """
    Print a border line for the receipt.
    """
    if width is None:
        width = RECEIPT_WIDTH
    if style == "top":
        print("┌" + "─" * width + "┐")
    elif style == "bottom":
        print("└" + "─" * width + "┘")


def print_line(content: str, width: int = None) -> None:
    """
    Print a line with borders on both sides.
    Content should be exactly 'width' characters.
    """
    if width is None:
        width = RECEIPT_WIDTH
    # Ensure content is exactly the right width
    if len(content) < width:
        content = content + " " * (width - len(content))
    elif len(content) > width:
        content = content[:width]
    print("│" + content + "│")


def wrap_two_column(
    label: str, value: str, width: int = None, padding: int = None
) -> None:
    """
    Print text in two-column format with wrapping.
    Left column shows the label, right column shows the value (right-aligned to the edge).
    Each column's content can be up to 45% of the usable width to maintain visual separation.
    Both columns will wrap if they exceed their maximum width.
    """
    if width is None:
        width = RECEIPT_WIDTH
    if padding is None:
        padding = RECEIPT_PADDING

    usable_width = width - (padding * 2)  # Account for both left and right padding
    max_col_width = int(
        usable_width * 0.45
    )  # Each column's content can use max 45% of width

    # Wrap right column (value) if needed
    value_lines = []
    current_value = value
    while len(current_value) > max_col_width:
        # Find last space or comma within max_col_width
        split_at = max(
            current_value[:max_col_width].rfind(" "),
            current_value[:max_col_width].rfind(",") + 1,  # +1 to include the comma
        )
        if split_at <= 0:  # No space or comma found, hard break
            split_at = max_col_width
        value_lines.append(current_value[:split_at].rstrip())
        current_value = current_value[split_at:].lstrip()
    if current_value:
        value_lines.append(current_value)

    # Print first line: label left-aligned, value right-aligned to the right edge
    if value_lines:
        gap = usable_width - len(label) - len(value_lines[0])
        content = " " * padding + label + " " * gap + value_lines[0] + " " * padding
        print_line(content, width)

    # Print remaining value lines (if wrapped), maintaining right-alignment to the edge
    for value_line in value_lines[1:]:
        gap = usable_width - len(value_line)
        content = " " * padding + " " * gap + value_line + " " * padding
        print_line(content, width)


def print_receipt(webhook: LinearWebhook) -> None:
    """
    Print a beautiful ASCII receipt for a newly created issue.
    Classic thermal receipt printer style with borders.

    Note: This function should only be called for Issue webhooks.
    """
    # Ensure we're handling an Issue webhook with proper data structure
    if webhook.type != "Issue":
        print(f"⚠️  print_receipt called with non-Issue webhook type: {webhook.type}")
        return

    data = webhook.data
    width = RECEIPT_WIDTH
    padding = RECEIPT_PADDING
    inner_width = RECEIPT_INNER_WIDTH

    print("\n")
    print_border_line(width, "top")

    print_line("", width)

    if COMPANY_NAME:
        print_line(
            " " * padding + COMPANY_NAME.center(inner_width) + " " * padding, width
        )
        print_line("", width)

    if COMPANY_ADDRESS_LINE1:
        print_line(
            " " * padding + COMPANY_ADDRESS_LINE1.center(inner_width) + " " * padding,
            width,
        )
    if COMPANY_ADDRESS_LINE2:
        print_line(
            " " * padding + COMPANY_ADDRESS_LINE2.center(inner_width) + " " * padding,
            width,
        )
    if COMPANY_ADDRESS_LINE3:
        print_line(
            " " * padding + COMPANY_ADDRESS_LINE3.center(inner_width) + " " * padding,
            width,
        )

    if COMPANY_PHONE:
        print_line(
            " " * padding + f"Tel: {COMPANY_PHONE}".center(inner_width) + " " * padding,
            width,
        )

    if COMPANY_URL:
        print_line(
            " " * padding + COMPANY_URL.center(inner_width) + " " * padding, width
        )

    print_line("", width)

    # Timestamp
    now = datetime.now().strftime("%b %d, %Y at %I:%M %p")
    print_line(" " * padding + now + " " * padding, width)
    print_line("", width)

    # Details in two-column format (label left, value right-aligned)
    wrap_two_column("Team", data.team.name, width)
    wrap_two_column("Priority", data.priorityLabel, width)
    wrap_two_column("Status", data.state.name, width)

    assignee_name = data.assignee.name if data.assignee else "Unassigned"
    wrap_two_column("Assignee", assignee_name, width)

    if data.dueDate:
        due = datetime.strptime(str(data.dueDate), "%Y-%m-%d").strftime("%b %d, %Y")
        wrap_two_column("Due", due, width)

    if data.labels:
        label_names = ", ".join([label.name for label in data.labels])
        wrap_two_column("Labels", label_names, width)

    wrap_two_column("Created by", webhook.actor.name, width)
    wrap_two_column("ID", data.identifier, width)
    print_line("", width)

    # Separator
    print_line(" " * padding + "─" * inner_width + " " * padding, width)
    print_line("", width)

    # TICKET TITLE - Most important!
    print_line(" " * padding + data.title.upper() + " " * padding, width)
    print_line("", width)

    # TICKET DESCRIPTION - Second most important!
    if data.description:
        desc = data.description.replace("\n", " ").strip()
        print_line(" " * padding + desc + " " * padding, width)
        print_line("", width)

    # Separator
    print_line(" " * padding + "─" * inner_width + " " * padding, width)
    print_line("", width)

    if COMPANY_TAGLINE:
        print_line(
            " " * padding + COMPANY_TAGLINE.center(inner_width) + " " * padding,
            width,
        )
        print_line("", width)

    print_border_line(width, "bottom")
    print()
