"""
Linear webhook router.
Handles incoming Linear webhooks and processes Issue creation events.
"""

import hmac
import hashlib
import json
import time
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from papercut.core.models import Ticket
from papercut.platforms.linear.models import LinearWebhook
from papercut.outputs.console import print_console_preview
from papercut.outputs.printer import print_to_printer
from config import LINEAR_SIGNING_SECRET


class WebhookResponse(BaseModel):
    """Response from webhook endpoint"""

    status: str = Field(..., description="Status of webhook processing")
    ignored: Optional[bool] = Field(None, description="Whether webhook was ignored")
    type: Optional[str] = Field(None, description="Event type")
    action: Optional[str] = Field(None, description="Action performed")
    timestamp: Optional[int] = Field(None, description="Unix timestamp in milliseconds")


class LinearAdapter:
    """Adapter to convert Linear webhooks to platform-agnostic Ticket model."""

    @staticmethod
    def to_ticket(webhook: LinearWebhook) -> Ticket:
        """
        Convert a Linear webhook to a platform-agnostic Ticket.

        Args:
            webhook: Linear webhook payload

        Returns:
            Ticket: Platform-agnostic ticket model
        """
        data = webhook.data
        return Ticket(
            id=data.id,
            identifier=data.identifier,
            title=data.title,
            description=data.description,
            status=data.state.name,
            priority=data.priorityLabel,
            assignee=data.assignee.name if data.assignee else None,
            labels=[label.name for label in data.labels],
            created_at=data.createdAt,
            created_by=webhook.actor.name,
            team=data.team.name,
            due_date=data.dueDate,
            url=data.url,
        )


def _verify_signature(payload_body: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature from Linear."""
    expected_signature = hmac.new(
        LINEAR_SIGNING_SECRET.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def _verify_timestamp(webhook_timestamp: int, max_age_seconds: int = 60) -> bool:
    """Verify webhook timestamp to prevent replay attacks."""
    current_time_ms = int(time.time() * 1000)
    age_ms = abs(current_time_ms - webhook_timestamp)
    return age_ms <= (max_age_seconds * 1000)


# Linear webhook router
router = APIRouter(tags=["Linear"])


@router.post("/linear", response_model=WebhookResponse, summary="Linear Webhook")
async def handle_webhook(request: Request) -> WebhookResponse:
    """
    Handle Linear webhooks.

    Processes Issue creation events and prints receipts.

    Security:
    - HMAC-SHA256 signature verification
    - Timestamp validation (60-second window)
    """
    # Verify signature
    signature = request.headers.get("Linear-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Linear-Signature header")

    payload_body = await request.body()

    if not _verify_signature(payload_body, signature):
        print("⚠️  Invalid signature - rejecting webhook")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON
    try:
        payload_dict = json.loads(payload_body)
    except json.JSONDecodeError as e:
        print(f"⚪ Ignoring malformed JSON: {e}")
        return WebhookResponse(status="received", ignored=True)

    # Verify timestamp
    webhook_timestamp = payload_dict.get("webhookTimestamp")
    if webhook_timestamp and not _verify_timestamp(webhook_timestamp):
        print("⚠️  Webhook timestamp too old - rejecting to prevent replay attack")
        raise HTTPException(
            status_code=401, detail="Webhook timestamp outside acceptable range"
        )

    # Only process Issue creation events
    webhook_type = payload_dict.get("type")
    webhook_action = payload_dict.get("action")

    if webhook_type != "Issue" or webhook_action != "create":
        print(f"⚪ Ignoring webhook: {webhook_type}:{webhook_action}")
        return WebhookResponse(status="received", ignored=True)

    # Parse and convert to platform-agnostic Ticket
    try:
        webhook = LinearWebhook(**payload_dict)
        ticket = LinearAdapter.to_ticket(webhook)

        # Output to console and printer
        print_console_preview(ticket)
        print_to_printer(ticket)

    except Exception as e:
        print(f"⚪ Ignoring unparsable webhook: {e}")
        return WebhookResponse(status="received", ignored=True)

    return WebhookResponse(
        status="received",
        type=webhook.type,
        action=webhook.action,
        timestamp=webhook.webhookTimestamp,
    )
