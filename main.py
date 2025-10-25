import hmac
import hashlib
import json
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
    payload_dict = json.loads(payload_body)

    # Parse into type-safe Pydantic model
    try:
        webhook = LinearWebhook(**payload_dict)
    except Exception as e:
        print(f"⚠️  Failed to parse webhook: {e}")
        # Still return 200 to Linear, but log the error
        return {"status": "received", "error": "parse_error"}

    # Handle specific events
    if webhook.type == "Issue" and webhook.action == "create":
        # Print the beautiful receipt! 🎫
        print_receipt(webhook)

        # Add your custom logic here
        # For example: send to actual thermal printer, save to database, etc.

    elif webhook.type == "Issue" and webhook.action == "update":
        print(f"\n📝 ISSUE UPDATED: {webhook.data.identifier}")
        if webhook.updatedFrom:
            print(f"   Changed fields: {', '.join(webhook.updatedFrom.keys())}")
        print()

    elif webhook.type == "Comment" and webhook.action == "create":
        print(f"\n💬 NEW COMMENT on {webhook.url}")
        print(f"   Author: {webhook.actor.name}")
        print()

    else:
        print(f"\n📌 Event: {webhook.type} - {webhook.action}")
        print()

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
