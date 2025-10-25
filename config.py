"""
Configuration settings for the Linear Ticket Printer.
Loads environment variables and defines application constants.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# Linear Webhook Configuration
# ============================================================================

LINEAR_SIGNING_SECRET = os.getenv("LINEAR_SIGNING_SECRET")
if not LINEAR_SIGNING_SECRET:
    raise ValueError("LINEAR_SIGNING_SECRET environment variable is not set")

# ============================================================================
# Company Information (for receipt header/footer)
# ============================================================================

COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
COMPANY_ADDRESS_LINE1 = os.getenv("COMPANY_ADDRESS_LINE1", "123 Main St")
COMPANY_ADDRESS_LINE2 = os.getenv("COMPANY_ADDRESS_LINE2", "City, State 12345")
COMPANY_ADDRESS_LINE3 = os.getenv("COMPANY_ADDRESS_LINE3", "")  # Optional third line
COMPANY_URL = os.getenv("COMPANY_URL", "https://krabby.dev")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+ 1 123 456 7890")
COMPANY_TAGLINE = os.getenv("COMPANY_TAGLINE", "Made with ❤️ by KaBanks")

# ============================================================================
# Receipt Formatting Constants
# ============================================================================

RECEIPT_WIDTH = 48  # Total width of the receipt (excluding borders)
RECEIPT_PADDING = 2  # Padding on both left and right sides
RECEIPT_INNER_WIDTH = RECEIPT_WIDTH - (RECEIPT_PADDING * 2)  # Usable width for content
