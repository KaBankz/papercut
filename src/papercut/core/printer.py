"""
Receipt printer output.
Prints tickets on physical receipt printers using python-escpos.
"""

import logging
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError, Error as EscposError

from papercut.core.models import Ticket
from config import (
    COMPANY_NAME,
    COMPANY_ADDRESS_LINE1,
    COMPANY_ADDRESS_LINE2,
    COMPANY_ADDRESS_LINE3,
    COMPANY_URL,
    COMPANY_PHONE,
    COMPANY_TAGLINE,
    PRINTER_USB_VENDOR_ID,
    PRINTER_USB_PRODUCT_ID,
    PRINTER_LOGO_PATH,
    PRINTER_QR_SIZE,
)

logger = logging.getLogger(__name__)


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

        # Company logo (if configured)
        if PRINTER_LOGO_PATH:
            try:
                # Print logo (centered alignment handled by printer)
                p.set(align="center")
                p.image(PRINTER_LOGO_PATH)
                p.text("\n")
            except Exception as e:
                logger.warning(
                    f"Failed to print logo '{PRINTER_LOGO_PATH}': {e}. "
                    "Note: Only PNG, JPG, GIF, and BMP formats are supported. "
                    "SVG files must be converted to PNG first."
                )

        # Company header - large, centered, bold
        if COMPANY_NAME:
            p.set(font="a", align="center", bold=True, width=2, height=2)
            p.text(COMPANY_NAME + "\n")
            p.set(font="a", align="center", bold=False, width=1, height=1)

        # Company address (centered)
        if COMPANY_ADDRESS_LINE1:
            p.text(COMPANY_ADDRESS_LINE1 + "\n")
        if COMPANY_ADDRESS_LINE2:
            p.text(COMPANY_ADDRESS_LINE2 + "\n")
        if COMPANY_ADDRESS_LINE3:
            p.text(COMPANY_ADDRESS_LINE3 + "\n")

        # Contact info
        if COMPANY_PHONE:
            p.text(COMPANY_PHONE + "\n")
        if COMPANY_URL:
            p.text(COMPANY_URL + "\n")

        # Timestamp
        p.set(align="center")
        p.text(ticket.created_at.strftime("\n" + "%b %d, %Y at %I:%M %p") + "\n\n")

        # Ticket details (left-aligned)
        p.set(align="left", bold=False, width=1, height=1)
        p.text(f"ID:       {ticket.identifier}\n")
        p.text(f"Team:     {ticket.team}\n")
        p.text(f"Priority: {ticket.priority}\n")
        p.text(f"Status:   {ticket.status}\n")

        if ticket.assignee:
            p.text(f"Assignee: {ticket.assignee}\n")

        if ticket.due_date:
            p.text(f"Due:      {ticket.due_date.strftime('%b %d, %Y')}\n")

        p.text(f"Creator:  {ticket.created_by}\n")

        # Labels (if any)
        if ticket.labels:
            p.text(f"Labels:   {', '.join(ticket.labels)}\n")

        # Title - bold, larger (automatically wraps)
        p.text("\n")
        p.set(bold=True, width=2, height=2)
        p.text(ticket.title.upper() + "\n")
        p.set(bold=False, width=1, height=1)

        # Description (if present)
        if ticket.description:
            p.text("\n")
            p.set(align="left")
            p.text(ticket.description + "\n")

        # QR code with ticket URL (centered)
        p.text("\n")
        p.set(align="center")
        p.text("Scan for details:\n")
        p.qr(ticket.url, size=PRINTER_QR_SIZE)
        p.text("\n")

        # Footer
        if COMPANY_TAGLINE:
            p.set(align="center", bold=False)
            p.text(COMPANY_TAGLINE + "\n\n")

        # Cut paper
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
