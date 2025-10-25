import hmac
import hashlib
import json
import os
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from models import LinearWebhook

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Linear Webhook Handler")

# Get signing key from environment variable
LINEAR_SIGNING_SECRET = os.getenv("LINEAR_SIGNING_SECRET")
if not LINEAR_SIGNING_SECRET:
    raise ValueError("LINEAR_SIGNING_SECRET environment variable is not set")


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

    # Parse the JSON payload into raw dict first for logging
    payload_dict = json.loads(payload_body)

    # Log the ENTIRE payload (formatted for readability)
    print("\n" + "=" * 80)
    print("📥 LINEAR WEBHOOK RECEIVED")
    print("=" * 80)
    print(json.dumps(payload_dict, indent=2))
    print("=" * 80 + "\n")

    # Parse into type-safe Pydantic model
    try:
        webhook = LinearWebhook(**payload_dict)
    except Exception as e:
        print(f"⚠️  Failed to parse webhook: {e}")
        # Still return 200 to Linear, but log the error
        return {"status": "received", "error": "parse_error"}

    # Now you have type-safe access to all properties!
    # Handle specific events
    if webhook.type == "Issue" and webhook.action == "create":
        print("✨ NEW ISSUE CREATED")
        print(f"   Title: {webhook.data.title}")
        print(f"   Identifier: {webhook.data.identifier}")
        print(f"   Priority: {webhook.data.priorityLabel}")
        print(f"   Team: {webhook.data.team.name} ({webhook.data.team.key})")
        print(f"   State: {webhook.data.state.name}")

        if webhook.data.assignee:
            print(
                f"   Assignee: {webhook.data.assignee.name} ({webhook.data.assignee.email})"
            )

        if webhook.data.dueDate:
            print(f"   Due Date: {webhook.data.dueDate}")

        if webhook.data.labels:
            label_names = [
                f"{label.name} ({label.color})" for label in webhook.data.labels
            ]
            print(f"   Labels: {', '.join(label_names)}")

        print(f"   URL: {webhook.url}")
        print(f"   Created by: {webhook.actor.name} ({webhook.actor.email})")

        if webhook.data.description:
            print(f"   Description: {webhook.data.description[:100]}...")

        # Add your custom logic here
        # For example: send to printer, save to database, send notification, etc.

    elif webhook.type == "Issue" and webhook.action == "update":
        if webhook.updatedFrom:
            print(f"📝 ISSUE UPDATED: {webhook.data.identifier}")
            print(f"   Changed fields: {', '.join(webhook.updatedFrom.keys())}")
        else:
            print(f"📝 ISSUE UPDATED: {webhook.data.identifier}")

    elif webhook.type == "Comment" and webhook.action == "create":
        print(f"💬 NEW COMMENT on {webhook.url}")
        print(f"   Author: {webhook.actor.name}")

    else:
        print(f"📌 Event: {webhook.type} - {webhook.action}")

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
