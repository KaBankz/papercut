"""
Receipt printer output.
Prints tickets on physical receipt printers using python-escpos.
"""

import logging
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError, Error as EscposError
import os
from papercut.core.models import Ticket
from config import (
    COMPANY_LOGO_PATH,
    COMPANY_NAME,
    COMPANY_ADDRESS_LINE1,
    COMPANY_ADDRESS_LINE2,
    COMPANY_URL,
    COMPANY_PHONE,
    COMPANY_TAGLINE,
    PRINTER_USB_VENDOR_ID,
    PRINTER_USB_PRODUCT_ID,
)

logger = logging.getLogger(__name__)


def _format_receipt_line(
    label: str,
    value: str,
    width: int = 48,  # 48 is standard for 80mm paper with Font A
) -> str:
    """
    Format a receipt line with label left-aligned and value right-aligned.

    This creates the classic receipt format with two columns:
    Label:              Value

    If the value is too long, it wraps to subsequent lines, right-aligned.

    Args:
        label: The label text (e.g., "ID:", "Team:")
        value: The value text
        width: Total character width of the receipt line (default: 48)

    Returns:
        Formatted string with proper spacing, possibly multi-line
    """
    # Maximum width for the value column (roughly half the receipt)
    max_value_width = width // 2

    # If value fits on one line with the label
    if len(value) <= max_value_width:
        spaces_needed = width - len(label) - len(value)
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
        if current_length + word_len <= max_value_width:
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
            spaces_needed = width - len(label) - len(line)
            if spaces_needed < 1:
                spaces_needed = 1
            result.append(f"{label}{' ' * spaces_needed}{line}\n")
        else:
            # Subsequent lines are right-aligned without label
            spaces_needed = width - len(line)
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
        # Convert hex string to int
        vendor_id = (
            int(PRINTER_USB_VENDOR_ID, 16)
            if isinstance(PRINTER_USB_VENDOR_ID, str)
            else PRINTER_USB_VENDOR_ID
        )
        product_id = (
            int(PRINTER_USB_PRODUCT_ID, 16)
            if isinstance(PRINTER_USB_PRODUCT_ID, str)
            else PRINTER_USB_PRODUCT_ID
        )
        logger.info(
            f"Connecting to USB printer: vendor={hex(vendor_id)}, product={hex(product_id)}"
        )
        return Usb(vendor_id, product_id)

    except USBNotFoundError as e:
        logger.error(
            f"USB printer not found. Check vendor/product IDs and USB connection: {e}"
        )
        raise
    except EscposError as e:
        logger.error(f"Error connecting to printer: {e}")
        raise


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
    try:
        p = _get_printer()

        if COMPANY_LOGO_PATH:
            if not os.path.exists(COMPANY_LOGO_PATH):
                logger.warning(f"Logo file not found: {COMPANY_LOGO_PATH}")
            else:
                try:
                    p.set(align="center")
                    p.image(COMPANY_LOGO_PATH)
                    p.text("\n")
                except Exception as e:
                    logger.warning(
                        f"Failed to print logo '{COMPANY_LOGO_PATH}': {e}. "
                        "Note: Only PNG, JPG, GIF, and BMP formats are supported. "
                        "SVG files must be converted to PNG first."
                    )

        if COMPANY_NAME:
            p.set(font="a", align="center", bold=True, width=2, height=2)
            p.text(COMPANY_NAME + "\n")
            p.set(font="a", align="center", bold=False, width=1, height=1)

        if COMPANY_ADDRESS_LINE1:
            p.text(COMPANY_ADDRESS_LINE1 + "\n")
        if COMPANY_ADDRESS_LINE2:
            p.text(COMPANY_ADDRESS_LINE2 + "\n")

        if COMPANY_PHONE:
            p.text(COMPANY_PHONE + "\n")
        if COMPANY_URL:
            p.text(COMPANY_URL + "\n")

        p.set(align="center")
        p.text(ticket.created_at.strftime("\n" + "%b %d, %Y at %I:%M %p") + "\n\n")

        # Ticket details (2-column layout: labels left, values right)
        p.set(align="left", bold=False, width=1, height=1)
        p.text(_format_receipt_line("ID:", ticket.identifier))
        p.text(_format_receipt_line("Team:", ticket.team))
        p.text(_format_receipt_line("Priority:", ticket.priority))
        p.text(_format_receipt_line("Status:", ticket.status))

        if ticket.assignee:
            p.text(_format_receipt_line("Assignee:", ticket.assignee))

        if ticket.due_date:
            p.text(_format_receipt_line("Due:", ticket.due_date.strftime("%b %d, %Y")))

        p.text(_format_receipt_line("Creator:", ticket.created_by))

        if ticket.labels:
            labels_text = ", ".join(ticket.labels)
            p.text(_format_receipt_line("Labels:", labels_text))

        # Title (max 350 chars to prevent crazy long receipts)
        p.text("\n")
        p.set(bold=True, width=2, height=2)
        title = ticket.title.strip()
        if len(title) > 350:
            title = title[:347] + "..."
        p.text(title + "\n")
        p.set(bold=False, width=1, height=1)

        # Description (max 350 chars to prevent crazy long receipts)
        if ticket.description:
            p.text("\n")
            p.set(align="left")
            description = ticket.description.strip()
            if len(description) > 350:
                description = description[:347] + "..."
            p.text(description + "\n")

        p.text("\n")
        p.set(align="center")
        p.text("Scan for details:\n")
        p.qr(ticket.url, size=6)
        p.text("\n")

        if COMPANY_TAGLINE:
            p.set(align="center", bold=False)
            p.text(COMPANY_TAGLINE + "\n\n")

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
