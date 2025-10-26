"""
Papercut FastAPI application.
Webhook endpoints for Linear and other platforms.
"""

import hmac
import hashlib
import json
import time
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from papercut.platforms.linear import LinearWebhook, LinearAdapter
from papercut.outputs.console import print_console_preview
from papercut.outputs.printer import print_to_printer
from config import LINEAR_SIGNING_SECRET

app = FastAPI(
    title="Papercut",
    description="Print your tickets on a real receipt printer",
    version="0.1.0",
)


class WebhookResponse(BaseModel):
    """Response from the webhook endpoint"""

    status: str = Field(..., description="Status of the webhook processing")
    ignored: Optional[bool] = Field(None, description="Whether the webhook was ignored")
    type: Optional[str] = Field(None, description="Type of event")
    action: Optional[str] = Field(None, description="Action that was performed")
    timestamp: Optional[int] = Field(None, description="Unix timestamp in milliseconds")


class HealthCheckResponse(BaseModel):
    """Response from the health check endpoint"""

    status: str = Field(..., description="Server status")
    message: str = Field(..., description="Status message")


def _verify_linear_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Linear.
    Linear uses HMAC SHA-256 to sign webhook payloads.
    """
    expected_signature = hmac.new(
        LINEAR_SIGNING_SECRET.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def _verify_webhook_timestamp(
    webhook_timestamp: int, max_age_seconds: int = 60
) -> bool:
    """
    Verify webhook timestamp to prevent replay attacks.
    Linear recommends checking within 60 seconds.
    """
    current_time_ms = int(time.time() * 1000)
    age_ms = abs(current_time_ms - webhook_timestamp)
    return age_ms <= (max_age_seconds * 1000)


@app.post("/webhooks/linear", response_model=WebhookResponse, summary="Linear Webhook")
async def linear_webhook(request: Request) -> WebhookResponse:
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

    if not _verify_linear_signature(payload_body, signature):
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
    if webhook_timestamp and not _verify_webhook_timestamp(webhook_timestamp):
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


@app.get("/", response_model=HealthCheckResponse, summary="Health Check")
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(status="ok", message="Papercut is running")
