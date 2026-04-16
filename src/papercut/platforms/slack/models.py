"""
Slack print request models.
Pydantic models for Slack bot print payloads.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SlackPrintRequest(BaseModel):
    """
    Print request from a Slack bot.

    The Slack bot sends pre-formatted content ready to print.
    Content is markdown with optional inline images using ![alt](url) syntax.

    Example payload:
        {
            "content": "# Order Receipt\\n\\nItem: Widget\\nPrice: $9.99\\n\\n![logo](https://example.com/logo.png)",
            "include_header": true,
            "include_footer": true,
            "footer_url": "https://example.com/order/123",
            "cut": true
        }
    """

    content: str = Field(
        ...,
        description="Markdown-formatted content to print. "
        "Supports headers, bold, italic, bullet lists, and inline images via ![alt](url) syntax.",
    )
    include_header: bool = Field(
        True,
        description="Whether to print the receipt header (logo, company info)",
    )
    include_footer: bool = Field(
        True,
        description="Whether to print the receipt footer",
    )
    footer_url: Optional[str] = Field(
        None,
        description="URL to encode as QR code in footer. If omitted, QR code is skipped.",
    )
    cut: bool = Field(
        True,
        description="Whether to cut the paper after printing",
    )
