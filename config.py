"""
Configuration settings for Papercut.
Loads environment variables and defines application constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Linear Webhook Configuration
LINEAR_SIGNING_SECRET = os.getenv("LINEAR_SIGNING_SECRET")
if not LINEAR_SIGNING_SECRET:
    raise ValueError("LINEAR_SIGNING_SECRET environment variable is not set")

# Company Information
COMPANY_LOGO_PATH = os.getenv("COMPANY_LOGO_PATH", "assets/logo.png")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
COMPANY_ADDRESS_LINE1 = os.getenv("COMPANY_ADDRESS_LINE1", "123 Main St")
COMPANY_ADDRESS_LINE2 = os.getenv("COMPANY_ADDRESS_LINE2", "City, State 12345")
COMPANY_ADDRESS_LINE3 = os.getenv("COMPANY_ADDRESS_LINE3", "")  # Optional third line
COMPANY_URL = os.getenv("COMPANY_URL", "https://krabby.dev")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+ 1 123 456 7890")
COMPANY_TAGLINE = os.getenv("COMPANY_TAGLINE", "Made with ❤️ by KaBanks")

# Console receipt formatting constants
RECEIPT_WIDTH = 48  # Total width of the receipt (excluding borders)
RECEIPT_PADDING = 2  # Padding on both left and right sides
RECEIPT_INNER_WIDTH = RECEIPT_WIDTH - (RECEIPT_PADDING * 2)  # Usable width for content

# Printer Configuration (USB Only)
# USB Printer Settings (default: Epson TM-T20III)
# Note: run `ioreg` to verify your device
PRINTER_USB_VENDOR_ID = os.getenv("PRINTER_USB_VENDOR_ID", "0x04b8")
PRINTER_USB_PRODUCT_ID = os.getenv("PRINTER_USB_PRODUCT_ID", "0x0e28")
# 48 is standard for 80mm paper with Font A
PRINTER_CHAR_WIDTH = int(os.getenv("PRINTER_CHAR_WIDTH", "48"))
