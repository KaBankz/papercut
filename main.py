import hmac
import hashlib
import json
import time
from fastapi import FastAPI, Request, HTTPException

from models import LinearWebhook
from config import LINEAR_SIGNING_SECRET
from ascii import print_receipt

app = FastAPI(title="Linear Webhook Handler")


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


@app.post("/")
async def handle_linear_webhook(request: Request):
    """
    Handle incoming webhooks from Linear.
    Linear will POST to this endpoint when events occur.
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
        return {"status": "received", "ignored": True}

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
        return {"status": "received", "ignored": True}

    # Parse into type-safe Pydantic model (only for Issue creation)
    try:
        webhook = LinearWebhook(**payload_dict)
        # Print the beautiful receipt! 🎫
        print_receipt(webhook)
    except Exception as e:
        # Silently ignore if parsing fails
        print(f"⚪ Ignoring unparseable webhook: {e}")
        return {"status": "received", "ignored": True}

    # Always return 200 OK so Linear knows we received it
    return {
        "status": "received",
        "type": webhook.type,
        "action": webhook.action,
        "timestamp": webhook.webhookTimestamp,
    }


@app.get("/")
async def root():
    """Health check endpoint - confirms the server is running"""
    return {"status": "ok", "message": "Linear webhook server is running"}


if __name__ == "__main__":
    import uvicorn

    # Run the server on port 8000
    # Note: For auto-reload during development, run with:
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
