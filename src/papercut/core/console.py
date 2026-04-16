"""
Console receipt preview.
Formats tickets as ASCII receipts for console logging.
"""

import re
from datetime import datetime, timezone

from papercut.core.models import Ticket
from papercut.core.utils import wrap_text, truncate_text, utc_to_local
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
    local_time = utc_to_local(ticket.created_at)
    created_at = local_time.strftime("%b %d, %Y at %I:%M %p").center(inner_width)
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
    title = truncate_text(ticket.title, config.providers.linear.max_title_length)
    title_lines = wrap_text(title, inner_width)
    for line in title_lines:
        _print_line(" " * padding + line + " " * padding, width)
    _print_line("", width)

    # Ticket description (wrapped)
    if ticket.description:
        desc = truncate_text(
            ticket.description, config.providers.linear.max_description_length
        )
        desc_lines = wrap_text(desc, inner_width)
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


# --- Pattern for markdown images: ![alt](url) ---
_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def print_raw_console_preview(
    content: str,
    include_header: bool = True,
    include_footer: bool = True,
    footer_url: str | None = None,
) -> None:
    """
    Print a console preview of raw/pre-formatted receipt content.

    Used for Slack bot and other raw print requests.
    Renders the content in an ASCII receipt box, replacing inline
    image references with placeholder text.

    Args:
        content: Markdown-formatted content to display
        include_header: Whether to show the receipt header
        include_footer: Whether to show the receipt footer
        footer_url: URL shown in footer (if any)
    """
    width = RECEIPT_WIDTH
    padding = RECEIPT_PADDING
    inner_width = RECEIPT_INNER_WIDTH

    print("\n")
    _print_border_line(width, "top")
    _print_line("", width)

    # Header (reuse same logic as ticket preview)
    if include_header:
        if config.header.company_name is not None:
            _print_line(
                " " * padding
                + config.header.company_name.center(inner_width)
                + " " * padding,
                width,
            )

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
                " " * padding + config.header.url.center(inner_width) + " " * padding,
                width,
            )

        _print_line("", width)

    # Timestamp
    now = datetime.now(timezone.utc)
    local_time = utc_to_local(now)
    timestamp = local_time.strftime("%b %d, %Y at %I:%M %p").center(inner_width)
    _print_line(" " * padding + timestamp + " " * padding, width)
    _print_line("", width)

    # Content - replace image references with placeholder text
    display_content = _IMAGE_PATTERN.sub(lambda m: f"[IMAGE: {m.group(2)}]", content)

    # Render content lines with wrapping
    for line in display_content.split("\n"):
        if line.strip() == "":
            _print_line("", width)
        else:
            wrapped = wrap_text(line, inner_width)
            for wrapped_line in wrapped:
                _print_line(" " * padding + wrapped_line + " " * padding, width)

    _print_line("", width)

    # Footer section
    if include_footer and not config.footer.disabled:
        if footer_url:
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
