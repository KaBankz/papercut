import hmac
import hashlib
import json
import time
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from models import LinearWebhook
from config import LINEAR_SIGNING_SECRET
from ascii import print_receipt

app = FastAPI(
    title="Papercut",
    description="Print your tickets on a real receipt printer",
    version="0.1.0",
)


class WebhookResponse(BaseModel):
    """Response from the webhook endpoint"""

    status: str = Field(..., description="Status of the webhook processing")
    ignored: Optional[bool] = Field(None, description="Whether the webhook was ignored")
    type: Optional[str] = Field(None, description="Type of Linear event")
    action: Optional[str] = Field(None, description="Action that was performed")
    timestamp: Optional[int] = Field(None, description="Unix timestamp in milliseconds")


class HealthCheckResponse(BaseModel):
    """Response from the health check endpoint"""

    status: str = Field(..., description="Server status")
    message: str = Field(..., description="Status message")


def verify_linear_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Linear by checking the signature.
    Linear uses HMAC SHA-256 to sign webhook payloads.
    """
    # Compute the expected signature
    expected_signature = hmac.new(
        LINEAR_SIGNING_SECRET.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()

    # Compare signatures (using constant-time comparison to prevent timing attacks)
    return hmac.compare_digest(expected_signature, signature)


def verify_webhook_timestamp(webhook_timestamp: int, max_age_seconds: int = 60) -> bool:
    """
    Verify that the webhook timestamp is recent to prevent replay attacks.
    Linear recommends checking that the timestamp is within 60 seconds.

    Args:
        webhook_timestamp: Unix timestamp in milliseconds from webhook payload
        max_age_seconds: Maximum age in seconds (default: 60)

    Returns:
        True if timestamp is within the acceptable range, False otherwise
    """
    current_time_ms = int(time.time() * 1000)
    age_ms = abs(current_time_ms - webhook_timestamp)
    return age_ms <= (max_age_seconds * 1000)


@app.post("/", response_model=WebhookResponse, summary="Linear Webhook Handler")
async def handle_linear_webhook(request: Request) -> WebhookResponse:
    """
    Handle incoming webhooks from Linear.

    This endpoint:
    - Verifies HMAC-SHA256 signature
    - Validates timestamp (60-second window)
    - Processes Issue:create events (prints receipt)
    - Silently ignores all other webhook types

    Security:
    - Requires `Linear-Signature` header
    - Rejects old webhooks (replay attack prevention)
    """
    # Get the signature from headers
    signature = request.headers.get("Linear-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Linear-Signature header")

    # Get the raw request body (needed for signature verification)
    payload_body = await request.body()

    # Verify the signature
    if not verify_linear_signature(payload_body, signature):
        print("⚠️  Invalid signature - rejecting webhook")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse the JSON payload
    try:
        payload_dict = json.loads(payload_body)
    except json.JSONDecodeError as e:
        # Silently ignore malformed JSON
        print(f"⚪ Ignoring malformed JSON: {e}")
        return WebhookResponse(status="received", ignored=True)

    # Verify webhook timestamp to prevent replay attacks
    webhook_timestamp = payload_dict.get("webhookTimestamp")
    if webhook_timestamp and not verify_webhook_timestamp(webhook_timestamp):
        print("⚠️  Webhook timestamp too old - rejecting to prevent replay attack")
        raise HTTPException(
            status_code=401, detail="Webhook timestamp outside acceptable range"
        )

    # Quick check: only process Issue creation events
    webhook_type = payload_dict.get("type")
    webhook_action = payload_dict.get("action")

    if webhook_type != "Issue" or webhook_action != "create":
        # Silently ignore all other webhook types/actions
        print(f"⚪ Ignoring webhook: {webhook_type}:{webhook_action}")
        return WebhookResponse(status="received", ignored=True)

    # Parse into type-safe Pydantic model (only for Issue creation)
    try:
        webhook = LinearWebhook(**payload_dict)
        # Print the beautiful receipt! 🎫
        print_receipt(webhook)
    except Exception as e:
        # Silently ignore if parsing fails
        print(f"⚪ Ignoring unparseable webhook: {e}")
        return WebhookResponse(status="received", ignored=True)

    # Always return 200 OK so Linear knows we received it
    return WebhookResponse(
        status="received",
        type=webhook.type,
        action=webhook.action,
        timestamp=webhook.webhookTimestamp,
    )


@app.get("/", response_model=HealthCheckResponse, summary="Health Check")
async def root() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns server status to confirm Papercut is running.
    """
    return HealthCheckResponse(status="ok", message="Papercut is running")


if __name__ == "__main__":
    import uvicorn

    # Run the server on port 8000
    # Note: For auto-reload during development, run with:
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
