# Papercut — _Issues you can touch_

Print your tickets on a real receipt printer.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Set Up Environment Variables

Create a `.env` file based on the `.env.example` in the project root.

> [!NOTE]
> Section 5 explains how to get your webhook URL and Linear signing secret.

All `COMPANY_` prefixed variables are optional, omitting them will fallback to default values, and passing an empty value will omit the line from the receipt.

### 3. Run the Server

**Development (with auto-reload):**

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server runs on `http://localhost:8000`

- Webhook: `POST http://localhost:8000/webhooks/linear`
- Health check: `GET http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

**Docker (Optional):**

```bash
make build && make compose-up
```

### 4. Expose to Internet

Use ngrok for development:

```bash
ngrok http 8000
```

### 5. Configure Linear Webhook

1. Go to Linear → Settings → API → Webhooks
2. Click "New Webhook"
3. Set URL to `https://your-domain.com/webhooks/linear` (or ngrok URL + `/webhooks/linear`)
4. Copy the signing secret to your `.env` file
5. Select: **Issues** → **created**
6. Save

## Printers

Tested on **EPSON TM-T88III**. Works with any standard receipt printer. (using python-escpos)

## Security

- HMAC-SHA256 signature verification
- Timestamp validation (prevents replay attacks)
- Only processes Issue creation webhooks

## Tech Stack

- FastAPI - Modern Python web framework
- Uvicorn - ASGI server
- uv - Fast package manager
- python-escpos - Receipt printer support
