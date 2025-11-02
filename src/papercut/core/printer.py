"""
Receipt printer output.
Prints tickets on physical receipt printers using python-escpos.
"""

import logging
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError, Error as EscposError
from papercut.core.models import Ticket
from config import config

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
        logger.info(
            f"Connecting to USB printer: vendor={hex(config.printer.usb_vendor_id)}, "
            f"product={hex(config.printer.usb_product_id)}"
        )
        return Usb(config.printer.usb_vendor_id, config.printer.usb_product_id)

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
            p.set(align="center")
            p.image(config.header.logo_path)
            p.text("\n")
        except Exception as e:
            logger.warning(
                f"Failed to print logo '{config.header.logo_path}': {e}. "
                "Note: Only PNG, JPG, GIF, and BMP formats are supported. "
                "SVG files must be converted to PNG first."
            )

    # Company name (large, bold)
    if config.header.company_name is not None:
        p.set(font="a", align="center", bold=True, width=2, height=2)
        p.text(config.header.company_name + "\n")
        p.set(font="a", align="center", bold=False, width=1, height=1)

    # Address lines
    if config.header.address_line1 is not None:
        p.text(config.header.address_line1 + "\n")
    if config.header.address_line2 is not None:
        p.text(config.header.address_line2 + "\n")

    # Contact info
    if config.header.phone is not None:
        p.text(config.header.phone + "\n")
    if config.header.url is not None:
        p.text(config.header.url + "\n")


def _print_footer(p, url: str) -> None:
    """
    Print receipt footer (QR code and footer text).

    Args:
        p: ESC/POS printer instance
        url: URL to encode in QR code
    """
    if config.footer.disabled:
        return

    p.text("\n")
    p.set(align="center")

    # QR code title
    if config.footer.qr_code_title is not None:
        p.text(config.footer.qr_code_title + "\n")

    # QR code
    if not config.footer.qr_code_disabled:
        p.qr(url, size=config.footer.qr_code_size)
        p.text("\n")

    # Footer text
    if config.footer.footer_text is not None:
        p.set(align="center", bold=False)
        p.text(config.footer.footer_text + "\n\n")


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

        # Print header
        _print_header(p)

        # Timestamp
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

        # Title
        p.text("\n")
        p.set(bold=True, width=2, height=2)
        title = ticket.title.strip()
        max_title_len = config.providers.linear.max_title_length
        if len(title) > max_title_len:
            title = title[: max_title_len - 3] + "..."
        p.text(title + "\n")
        p.set(bold=False, width=1, height=1)

        # Description
        if ticket.description:
            p.text("\n")
            p.set(align="left")
            description = ticket.description.strip()
            max_desc_len = config.providers.linear.max_description_length
            if len(description) > max_desc_len:
                description = description[: max_desc_len - 3] + "..."
            p.text(description + "\n")

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
