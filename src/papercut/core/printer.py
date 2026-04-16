"""
Receipt printer output.
Prints tickets on physical receipt printers using python-escpos.
"""

import logging
import re
import urllib.request
from io import BytesIO
from datetime import datetime, timezone

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
            profile=config.printer.profile,
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


# --- Image pattern for markdown inline images: ![alt](url) ---
_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _download_and_print_image(p, url: str, center: bool = True) -> None:
    """
    Download an image from a URL and print it on the receipt printer.

    Downloads the image into memory, opens it with PIL (already available
    via python-escpos), and prints it. If the download or printing fails,
    a placeholder text line is printed instead.

    Args:
        p: ESC/POS printer instance
        url: URL of the image to download
        center: Whether to center the image on the receipt
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Papercut/0.1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            image_data = response.read()

        from PIL import Image

        img = Image.open(BytesIO(image_data))

        p.image(img, center=center)
        p.ln()

        logger.debug(f"Printed image from {url} ({img.size[0]}x{img.size[1]})")

    except Exception as e:
        logger.warning(f"Failed to download/print image from '{url}': {e}")
        # Print placeholder text so content flow isn't silently broken
        p.set_with_default(align="center")
        p.textln(f"[Image: {url}]")
        p.set_with_default()


def _render_content_with_images(p, content: str) -> None:
    """
    Render markdown content that may contain inline images.

    Splits the content on markdown image syntax ![alt](url), renders
    each text segment as markdown, and downloads/prints each image
    inline in the content flow.

    Args:
        p: ESC/POS printer instance
        content: Markdown content potentially containing ![alt](url) references
    """
    from papercut.core.markdown import render_markdown_to_receipt

    last_end = 0
    for match in _IMAGE_PATTERN.finditer(content):
        # Render text before this image
        text_before = content[last_end : match.start()]
        if text_before.strip():
            render_markdown_to_receipt(p, text_before)

        # Download and print the image
        image_url = match.group(2)
        logger.info(f"Processing inline image: {image_url}")
        _download_and_print_image(p, image_url)

        last_end = match.end()

    # Render remaining text after last image (or all text if no images)
    remaining = content[last_end:]
    if remaining.strip():
        render_markdown_to_receipt(p, remaining)


def print_raw_receipt(
    content: str,
    include_header: bool = True,
    include_footer: bool = True,
    footer_url: str | None = None,
    cut: bool = True,
) -> None:
    """
    Print pre-formatted content on the receipt printer.

    Used for raw/pre-formatted print requests (e.g., from a Slack bot)
    where the caller controls the content layout. Supports markdown
    formatting and inline images via ![alt](url) syntax.

    Args:
        content: Markdown-formatted content to print
        include_header: Whether to print the receipt header (logo, company info)
        include_footer: Whether to print the receipt footer
        footer_url: URL to encode as QR code in footer (if None, QR code is skipped)
        cut: Whether to cut the paper after printing

    Raises:
        USBNotFoundError: If USB printer not found
        EscposError: For other printer errors
    """
    p = None
    try:
        p = _get_printer()

        # Initialize printer to clean state
        p.hw("INIT")

        # Header
        if include_header:
            _print_header(p)

        # Timestamp
        p.set_with_default(align="center")
        now = datetime.now(timezone.utc)
        p.textln(utc_to_local(now).strftime("%b %d, %Y at %I:%M %p"))
        p.set_with_default()
        p.ln()

        # Render content (markdown + inline images)
        _render_content_with_images(p, content)

        # Footer
        if include_footer and not config.footer.disabled:
            if footer_url:
                _print_footer(p, footer_url)
            else:
                # Print footer text without QR code
                p.ln(2)
                p.set_with_default(align="center")
                if config.footer.footer_text is not None:
                    p.set(underline=True)
                    p.textln(config.footer.footer_text)
                p.set_with_default()

        if cut:
            p.cut()

        logger.info("Successfully printed raw receipt")

    except USBNotFoundError:
        logger.error("Failed to print raw receipt: USB printer not found")
        raise
    except EscposError as e:
        logger.error(f"Failed to print raw receipt: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error printing raw receipt: {e}")
        raise
    finally:
        if p is not None:
            try:
                p.close()
                logger.debug("Printer connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing printer connection: {e}")
