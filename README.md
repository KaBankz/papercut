# Papercut

> Issues you can touch

Print your tickets on a real receipt printer.

## Why?

New Linear issue? Get a receipt. Stay in flow, skip the context switch.

Works with standard receipt printers like the EPSON TM-T88III.

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Create a `.env` file:

```bash
# Required
LINEAR_SIGNING_SECRET=lin_wh_YOUR_SIGNING_SECRET_HERE

# Optional - Company info for receipt header
COMPANY_NAME=Your Company
COMPANY_ADDRESS_LINE1=123 Main St
COMPANY_ADDRESS_LINE2=City, State 12345
COMPANY_ADDRESS_LINE3=
COMPANY_PHONE=+1 123 456 7890
COMPANY_URL=https://example.com
COMPANY_TAGLINE=Your tagline here
```

### 3. Run the Server

```bash
# Development
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uv run python main.py
```

Server runs on `http://localhost:8000`

- Webhook: `POST http://localhost:8000/`
- Health check: `GET http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

### 4. Docker (Optional)

```bash
make build && make compose-up
```

### 5. Expose to Internet

Use ngrok for development:

```bash
ngrok http 8000
```

### 6. Configure Linear Webhook

1. Go to Linear → Settings → API → Webhooks
2. Click "New Webhook"
3. Set URL to your public URL (or ngrok URL)
4. Copy the signing secret to your `.env` file
5. Select: **Issues** → **created**
6. Save

## Printers

Tested on **EPSON TM-T88III**. Works with any standard receipt printer.

Printer support coming when hardware arrives (using python-escpos).

## Security

- HMAC-SHA256 signature verification
- Timestamp validation (prevents replay attacks)
- Only processes Issue creation webhooks

## Tech Stack

- FastAPI - Modern Python web framework
- Uvicorn - ASGI server
- uv - Fast package manager
- python-escpos - Receipt printer support (coming soon)
