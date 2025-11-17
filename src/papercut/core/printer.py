"""
Receipt printer output.
Prints tickets on physical receipt printers using python-escpos.
"""

import logging
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError, Error as EscposError
from papercut.core.models import Ticket
from papercut.core.utils import truncate_text, utc_to_local
from config import config

logger = logging.getLogger(__name__)


def _format_receipt_line(
    p: Usb,
    label: str,
    value: str,
) -> str:
    """
    Format a receipt line with label left-aligned and value right-aligned.

    This creates the classic receipt format with two columns:
    Label:              Value

    If the value is too long, it wraps to subsequent lines, right-aligned.

    Args:
        label: The label text (e.g., "ID:", "Team:")
        value: The value text

    Returns:
        Formatted string with proper spacing, possibly multi-line
    """
    # Maximum width for the value column (roughly half the receipt)
    max_col_count = p.profile.get_columns(font="a")
    max_col_width = max_col_count // 2

    # If value fits on one line with the label
    if len(value) <= max_col_width:
        spaces_needed = max_col_count - len(label) - len(value)
        if spaces_needed < 1:
            spaces_needed = 1
        return f"{label}{' ' * spaces_needed}{value}\n"

    # Value is too long - need to wrap it, right-aligned
    lines = []
    words = value.split()
    current_line = []
    current_length = 0

    for word in words:
        word_len = len(word) + (1 if current_line else 0)  # +1 for space between words
        if current_length + word_len <= max_col_width:
            current_line.append(word)
            current_length += word_len
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    # Format the output
    result = []
    for i, line in enumerate(lines):
        if i == 0:
            # First line includes the label
            spaces_needed = max_col_count - len(label) - len(line)
            if spaces_needed < 1:
                spaces_needed = 1
            result.append(f"{label}{' ' * spaces_needed}{line}\n")
        else:
            # Subsequent lines are right-aligned without label
            spaces_needed = max_col_count - len(line)
            result.append(f"{' ' * spaces_needed}{line}\n")

    return "".join(result)


def _get_printer():
    """
    Get a USB printer instance.

    Returns:
        USB printer instance configured with vendor/product IDs.

    Raises:
        USBNotFoundError: If USB printer not found
        EscposError: For other printer connection errors
    """
    try:
        logger.info(
            f"Connecting to USB printer: vendor={hex(config.printer.usb_vendor_id)}, "
            f"product={hex(config.printer.usb_product_id)}"
        )
        return Usb(
            idVendor=config.printer.usb_vendor_id,
            idProduct=config.printer.usb_product_id,
            profile="TM-T20II",
        )

    except USBNotFoundError as e:
        logger.error(
            f"USB printer not found. Check vendor/product IDs and USB connection: {e}"
        )
        raise
    except EscposError as e:
        logger.error(f"Error connecting to printer: {e}")
        raise


def _print_header(p) -> None:
    """
    Print receipt header (logo and company info).

    Args:
        p: ESC/POS printer instance
    """

    # Logo
    if config.header.logo_path is not None:
        try:
            p.image(config.header.logo_path, center=True)
            p.ln()
        except Exception as e:
            logger.warning(
                f"Failed to print logo '{config.header.logo_path}': {e}. "
                "Note: Only PNG, JPG, GIF, and BMP formats are supported. "
                "SVG files must be converted to PNG first."
            )

    # Company name (large, bold)
    if config.header.company_name is not None:
        p.set(
            font="b", align="center", bold=True, double_height=True, double_width=True
        )
        p.textln(config.header.company_name)
        p.ln()

    p.set_with_default(align="center")

    # Address lines
    if config.header.address_line1 is not None:
        p.textln(config.header.address_line1)
    if config.header.address_line2 is not None:
        p.textln(config.header.address_line2)

    # Contact info
    if config.header.phone is not None:
        p.textln(config.header.phone)
    if config.header.url is not None:
        p.textln(config.header.url)

    p.ln()
    p.set_with_default()


def _print_footer(p, url: str) -> None:
    """
    Print receipt footer (QR code and footer text).

    Args:
        p: ESC/POS printer instance
        url: URL to encode in QR code
    """
    if config.footer.disabled:
        return

    p.ln(2)
    p.set_with_default(align="center")

    # QR code title
    if config.footer.qr_code_title is not None:
        p.textln(config.footer.qr_code_title)

    # QR code
    if not config.footer.qr_code_disabled:
        p.qr(url, size=config.footer.qr_code_size, native=True)
        p.ln()

    # Footer text
    if config.footer.footer_text is not None:
        p.set(underline=True)
        p.textln(config.footer.footer_text)

    p.set_with_default()


def print_to_printer(ticket: Ticket) -> None:
    """
    Print ticket on a receipt printer.

    Uses python-escpos for rich formatting including:
    - Variable font sizes (large title, small details)
    - Bold/underline emphasis
    - Company logo images
    - QR codes with ticket URL
    - Professional receipt layout

    Compatible with any standard receipt printer (EPSON TM-T88III, etc.)

    Args:
        ticket: The ticket to print

    Raises:
        USBNotFoundError: If USB printer not found
        EscposError: For other printer errors
    """
    p = None
    try:
        p = _get_printer()

        # Initialize printer to clean state
        p.hw("INIT")

        # Print header
        _print_header(p)

        # Timestamp
        p.set_with_default(align="center")
        p.textln(utc_to_local(ticket.created_at).strftime("%b %d, %Y at %I:%M %p"))

        p.set_with_default()

        # Ticket details (2-column layout: labels left, values right)
        p.text(_format_receipt_line(p, "ID:", ticket.identifier))
        p.text(_format_receipt_line(p, "Team:", ticket.team))
        p.text(_format_receipt_line(p, "Priority:", ticket.priority))
        p.text(_format_receipt_line(p, "Status:", ticket.status))

        if ticket.project:
            p.text(_format_receipt_line(p, "Project:", ticket.project))

        if ticket.milestone:
            milestone_text = ticket.milestone
            if ticket.milestone_date:
                milestone_text += f" ({ticket.milestone_date.strftime('%b %d')})"
            p.text(_format_receipt_line(p, "Milestone:", milestone_text))

        if ticket.assignee:
            p.text(_format_receipt_line(p, "Assignee:", ticket.assignee))

        if ticket.due_date:
            p.text(
                _format_receipt_line(p, "Due:", ticket.due_date.strftime("%b %d, %Y"))
            )

        p.text(_format_receipt_line(p, "Creator:", ticket.created_by))

        if ticket.labels:
            labels_text = ", ".join(ticket.labels)
            p.text(_format_receipt_line(p, "Labels:", labels_text))

        # Title
        p.ln()
        p.set(font="b", bold=True, double_height=True, double_width=True)
        title = truncate_text(ticket.title, config.providers.linear.max_title_length)
        # half the col count since font size is doubled
        columns = p.profile.get_columns(font="b") // 2
        p.block_text(title, columns=columns)

        p.set_with_default()

        # Description
        if ticket.description:
            p.ln(2)
            from papercut.core.markdown import render_markdown_to_receipt

            description = truncate_text(
                ticket.description, config.providers.linear.max_description_length
            )
            render_markdown_to_receipt(p, description)

        # Print footer
        _print_footer(p, ticket.url)

        p.cut()

        logger.info(f"Successfully printed ticket {ticket.identifier}")

    except USBNotFoundError:
        logger.error(
            f"Failed to print ticket {ticket.identifier}: USB printer not found"
        )
        raise
    except EscposError as e:
        logger.error(f"Failed to print ticket {ticket.identifier}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error printing ticket {ticket.identifier}: {e}")
        raise
    finally:
        # Always close the printer connection to release the USB device
        if p is not None:
            try:
                p.close()
                logger.debug("Printer connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing printer connection: {e}")
