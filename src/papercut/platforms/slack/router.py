"""
Slack webhook router.
Handles incoming print requests from a Slack bot.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from papercut.core.console import print_raw_console_preview
from papercut.core.printer import print_raw_receipt
from papercut.platforms.slack.models import SlackPrintRequest
from config import config

logger = logging.getLogger(__name__)


class SlackWebhookResponse(BaseModel):
    """Response from Slack webhook endpoint"""

    status: str = Field(..., description="Status of print request")
    message: Optional[str] = Field(None, description="Status message")
    content_length: Optional[int] = Field(
        None, description="Length of content received"
    )


def _verify_auth_token(authorization: str | None) -> None:
    """
    Verify bearer token authentication if configured.

    Args:
        authorization: Authorization header value

    Raises:
        HTTPException: If auth is required but token is missing or invalid
    """
    expected_token = config.providers.slack.auth_token

    # No auth configured - allow all requests
    if not expected_token:
        return

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Expect "Bearer <token>" format
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
        )

    if parts[1] != expected_token:
        logger.warning("Invalid auth token - rejecting request")
        raise HTTPException(status_code=401, detail="Invalid auth token")


# Slack webhook router
router = APIRouter(tags=["Slack"])


@router.post(
    "/slack", response_model=SlackWebhookResponse, summary="Slack Print Webhook"
)
async def handle_slack_print(
    request: SlackPrintRequest,
    authorization: Optional[str] = Header(None),
) -> SlackWebhookResponse:
    """
    Handle print requests from a Slack bot.

    Receives pre-formatted markdown content and prints it on the receipt printer.
    Supports inline images via markdown ![alt](url) syntax.

    Security:
    - Optional bearer token authentication (if auth_token is configured)
    """
    # Verify auth token if configured
    _verify_auth_token(authorization)

    # Truncate content if needed
    max_length = config.providers.slack.max_content_length
    content = request.content
    if len(content) > max_length:
        content = content[:max_length]
        logger.info(
            f"Content truncated from {len(request.content)} to {max_length} characters"
        )

    logger.info(f"Received Slack print request ({len(content)} chars)")

    # Print to console and printer
    try:
        print_raw_console_preview(
            content=content,
            include_header=request.include_header,
            include_footer=request.include_footer,
            footer_url=request.footer_url,
        )
        print_raw_receipt(
            content=content,
            include_header=request.include_header,
            include_footer=request.include_footer,
            footer_url=request.footer_url,
            cut=request.cut,
        )
    except Exception as e:
        logger.error(f"Error printing Slack content: {e}")

    return SlackWebhookResponse(
        status="printed",
        message="Content sent to printer",
        content_length=len(content),
    )
