import hmac
import hashlib
import json
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from models import LinearWebhook

load_dotenv()

app = FastAPI(title="Linear Webhook Handler")

LINEAR_SIGNING_SECRET = os.getenv("LINEAR_SIGNING_SECRET")
if not LINEAR_SIGNING_SECRET:
    raise ValueError("LINEAR_SIGNING_SECRET environment variable is not set")

COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
COMPANY_ADDRESS_LINE1 = os.getenv("COMPANY_ADDRESS_LINE1", "123 Main St")
COMPANY_ADDRESS_LINE2 = os.getenv("COMPANY_ADDRESS_LINE2", "City, State 12345")
COMPANY_ADDRESS_LINE3 = os.getenv("COMPANY_ADDRESS_LINE3", "")  # Optional third line
COMPANY_URL = os.getenv("COMPANY_URL", "https://krabby.dev")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+ 1 123 456 7890")
COMPANY_TAGLINE = os.getenv("COMPANY_TAGLINE", "Made with ❤️ by KaBanks")


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


def print_border_line(width: int = 48, style: str = "top") -> None:
    """
    Print a border line for the receipt.
    """
    if style == "top":
        print("┌" + "─" * width + "┐")
    elif style == "bottom":
        print("└" + "─" * width + "┘")


def print_line(content: str, width: int = 48) -> None:
    """
    Print a line with borders on both sides.
    Content should be exactly 'width' characters.
    """
    # Ensure content is exactly the right width
    if len(content) < width:
        content = content + " " * (width - len(content))
    elif len(content) > width:
        content = content[:width]
    print("│" + content + "│")


def wrap_two_column(label: str, value: str, width: int = 48, padding: int = 2) -> None:
    """
    Print text in two-column format with wrapping.
    Left column shows the label, right column shows the value (right-aligned to the edge).
    Each column's content can be up to 45% of the usable width to maintain visual separation.
    Both columns will wrap if they exceed their maximum width.
    """
    usable_width = width - (padding * 2)  # Account for both left and right padding
    max_col_width = int(
        usable_width * 0.45
    )  # Each column's content can use max 45% of width

    # Wrap right column (value) if needed
    value_lines = []
    current_value = value
    while len(current_value) > max_col_width:
        # Find last space or comma within max_col_width
        split_at = max(
            current_value[:max_col_width].rfind(" "),
            current_value[:max_col_width].rfind(",") + 1,  # +1 to include the comma
        )
        if split_at <= 0:  # No space or comma found, hard break
            split_at = max_col_width
        value_lines.append(current_value[:split_at].rstrip())
        current_value = current_value[split_at:].lstrip()
    if current_value:
        value_lines.append(current_value)

    # Print first line: label left-aligned, value right-aligned to the right edge
    if value_lines:
        gap = usable_width - len(label) - len(value_lines[0])
        content = " " * padding + label + " " * gap + value_lines[0] + " " * padding
        print_line(content, width)

    # Print remaining value lines (if wrapped), maintaining right-alignment to the edge
    for value_line in value_lines[1:]:
        gap = usable_width - len(value_line)
        content = " " * padding + " " * gap + value_line + " " * padding
        print_line(content, width)


def print_receipt(webhook: LinearWebhook) -> None:
    """
    Print a beautiful ASCII receipt for a newly created issue.
    Classic thermal receipt printer style with borders.
    """
    data = webhook.data
    width = 48
    padding = 2  # Padding on both left and right sides
    inner_width = width - (padding * 2)

    # Top border
    print("\n")
    print_border_line(width, "top")

    # Empty line
    print_line("", width)

    # Company header - centered within padded area
    print_line(" " * padding + COMPANY_NAME.center(inner_width) + " " * padding, width)
    print_line("", width)

    # Company address (multiple lines)
    if COMPANY_ADDRESS_LINE1:
        print_line(
            " " * padding + COMPANY_ADDRESS_LINE1.center(inner_width) + " " * padding,
            width,
        )
    if COMPANY_ADDRESS_LINE2:
        print_line(
            " " * padding + COMPANY_ADDRESS_LINE2.center(inner_width) + " " * padding,
            width,
        )
    if COMPANY_ADDRESS_LINE3:
        print_line(
            " " * padding + COMPANY_ADDRESS_LINE3.center(inner_width) + " " * padding,
            width,
        )

    print_line(
        " " * padding + f"Tel: {COMPANY_PHONE}".center(inner_width) + " " * padding,
        width,
    )
    print_line(" " * padding + COMPANY_URL.center(inner_width) + " " * padding, width)
    print_line("", width)

    # Timestamp
    now = datetime.now().strftime("%b %d, %Y at %I:%M %p")
    print_line(" " * padding + now + " " * padding, width)
    print_line("", width)

    # Details in two-column format (label left, value right-aligned)
    wrap_two_column("Team", data.team.name, width)
    wrap_two_column("Priority", data.priorityLabel, width)
    wrap_two_column("Status", data.state.name, width)

    assignee_name = data.assignee.name if data.assignee else "Unassigned"
    wrap_two_column("Assignee", assignee_name, width)

    if data.dueDate:
        due = datetime.strptime(str(data.dueDate), "%Y-%m-%d").strftime("%b %d, %Y")
        wrap_two_column("Due", due, width)

    if data.labels:
        label_names = ", ".join([label.name for label in data.labels])
        wrap_two_column("Labels", label_names, width)

    wrap_two_column("Created by", webhook.actor.name, width)
    wrap_two_column("ID", data.identifier, width)
    print_line("", width)

    # Separator
    print_line(" " * padding + "─" * inner_width + " " * padding, width)
    print_line("", width)

    # TICKET TITLE - Most important!
    print_line(" " * padding + data.title.upper() + " " * padding, width)
    print_line("", width)

    # TICKET DESCRIPTION - Second most important!
    if data.description:
        desc = data.description.replace("\n", " ").strip()
        print_line(" " * padding + desc + " " * padding, width)
        print_line("", width)

    # Separator
    print_line(" " * padding + "─" * inner_width + " " * padding, width)
    print_line("", width)

    # Footer tagline - centered within padded area
    print_line(
        " " * padding + COMPANY_TAGLINE.center(inner_width) + " " * padding,
        width,
    )
    print_line("", width)

    # Bottom border
    print_border_line(width, "bottom")
    print()


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
